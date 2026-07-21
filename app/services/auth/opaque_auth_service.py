from typing import Literal, Any
from datetime import timedelta, datetime
from zoneinfo import ZoneInfo
from app.core.local_config import settings
from app.repositories.in_memory_database.redis_repository import RedisAsyncRepository
from fastapi import Request, Response, HTTPException, status
import secrets
from app.core.logger import app_logger


class OpaqueAuthService:
    _zone_info = ZoneInfo("Asia/Manila")
    def __init__(
            self,
            redis_repository: RedisAsyncRepository,
            request: Request,
            response: Response
    ):
        self.redis_repo = redis_repository
        self.request = request
        self.response = response

    @property
    def secure(self) -> bool:
        if settings.project_development_mode:
            return False
        return True

    def error_503(self,message: str, ex = None):
        log_details = f"Details: {message}"
        if ex:
            log_details += f" // Exception: {str(ex)}"
        app_logger.error(log_details)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")

    def error_401(self,message: str, ex = None):
        log_details = f"Details: {message}"
        if ex:
            log_details += f" // Exception: {str(ex)}"
        app_logger.error(log_details)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")




    async def create_opaque_token_redis(self, input_id: str, token_type: Literal["access", "refresh"]):
        try:
            opaque_token_key = secrets.token_urlsafe(32)

            if token_type == "access":
                exp_time = timedelta(minutes=5)
            else:
                exp_time = timedelta(days=15)

            token_value = {
                "user_id": input_id,
                "date_created": datetime.now(self._zone_info).isoformat(),
                "token_type": token_type,
            }
            if await self.redis_repo.add_value(
                    input_key=opaque_token_key,
                    input_value=token_value,
                    exp=exp_time
            ):
                return opaque_token_key
            self.error_503(message="Opaque token failed to add values to redis")
        except Exception as ex:
            self.error_503(ex=ex, message="Redis opaque token creation failed")



    async def create_http_cookie(self, token_type: Literal["access", "refresh"], input_id: str):
        try:
            if token_type == "access":
                samesite = "lax"
                exp_time = timedelta(minutes=5)
            else:
                samesite = "strict"
                exp_time = timedelta(days=15)


            max_age = int(exp_time.total_seconds())

            opaque_token = await self.create_opaque_token_redis(input_id=input_id, token_type=token_type)

            self.response.set_cookie(
                key=token_type,
                value=opaque_token,
                max_age=max_age,
                samesite=samesite,
                httponly=True,
                secure=self.secure,
                path="/"
            )

            return opaque_token
        except HTTPException:
            raise
        except Exception as ex:
            raise self.error_401(ex=ex, message="HTTP Cookie creation failed")

    def get_raw_token_from_http_cookie(self, token_type: Literal["access", "refresh"]):
        raw_token = self.request.cookies.get(token_type, None)
        if raw_token is None:
            return None
        return raw_token



    @staticmethod
    def _user_data_to_user_id(user_data:dict | None):
        if user_data is None:
            return None
        return user_data.get("user_id", None)



    async def _get_access_user_id(self):
        access_token = self.get_raw_token_from_http_cookie("access")

        if access_token:
            user_data = await self.redis_repo.get_value(input_key=access_token)
            user_id = self._user_data_to_user_id(user_data=user_data)

            if user_id is not None:
                return user_id

        return None



    async def _get_refresh_user_id(self):
        refresh_token = self.get_raw_token_from_http_cookie("refresh")

        if refresh_token:
            user_data = await self.redis_repo.get_value(input_key=refresh_token)
            user_id = self._user_data_to_user_id(user_data=user_data)

            if user_id is not None:
                return user_id

        return None



    async def _rotate_cookies(
            self,
            user_id: str,
            refresh_token: str | None,
            access_token: str | None
    ):
        try:
            if access_token:
                await self.redis_repo.delete_value(input_key=access_token)
            if refresh_token:
                await self.redis_repo.delete_value(input_key=refresh_token)

            await self.create_http_cookie("access", user_id)
            await self.create_http_cookie("refresh", user_id)
        except HTTPException:
            raise
        except Exception as ex:
            self.error_401(ex=ex, message="Rotational Cookie creation failed")

    async def login_user(self, user_id):
        try:
            await self.create_http_cookie("access", user_id)
            await self.create_http_cookie("refresh", user_id)
        except HTTPException:
            raise
        except Exception as ex:
            self.error_401(ex=ex, message="User unexpectedly failed to logged in")

    async def logout_user(self):
        access_token = self.get_raw_token_from_http_cookie("access")
        refresh_token = self.get_raw_token_from_http_cookie("refresh")
        await self.redis_repo.delete_value(input_key=access_token)
        await self.redis_repo.delete_value(input_key=refresh_token)
        self.response.delete_cookie(key="access", path="/")
        self.response.delete_cookie(key="refresh", path="/")



    async def get_user_id(self):
        access_token = self.get_raw_token_from_http_cookie("access")
        refresh_token = self.get_raw_token_from_http_cookie("refresh")

        acc_user_id = await self._get_access_user_id()
        if acc_user_id:
            return acc_user_id

        ref_user_id = await self._get_refresh_user_id()
        if ref_user_id:
            await self._rotate_cookies(
                user_id=ref_user_id,
                access_token=access_token,
                refresh_token=refresh_token
            )
            return ref_user_id
        return None

    async def block_re_login_user(self, _id: Any):
        browser_user_id = await self.get_user_id()
        app_logger.debug("Starting to check user to block re-login")
        if _id and browser_user_id:
            if _id == browser_user_id:
                app_logger.debug(f"Failing User:{_id} to re-log as there is still user existing in cookies.")
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User already logged in to your device")


