from datetime import datetime, timezone, timedelta
from typing import Any
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
from src.core.local_config import settings
from src.data_storage.short_term_memory_store import JwtRedisStore
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from fastapi import Request, Response, HTTPException
import asyncio
import ulid



_password_hasher = PasswordHasher()

access_age = int(timedelta(minutes=5).total_seconds())
refresh_age = int(timedelta(days=15).total_seconds())


class SecurityAuth:
    def __init__(self, is_development: bool = True):
        self._is_development = is_development
        self._ph = _password_hasher
        self.secret_key = settings.groq_api_key.get_secret_value()
        self.algorithm = "HS256"
        self.jti_memory = JwtRedisStore()

    @property
    def ph(self) -> PasswordHasher:
        return self._ph

    @property
    def secure_cookie(self):
        if self._is_development:
            return False
        return True

    def _generate_token(self, sub: str):
        jti_id = str(ulid.new())
        time_now = datetime.now(timezone.utc)
        access_payload = {
            "sub": sub,
            "exp": time_now + timedelta(minutes=5),
            "iat": time_now,
            "type": "access",
            "jti": jti_id
        }
        refresh_payload = {
            "sub": sub,
            "exp": time_now + timedelta(days=15),
            "iat": time_now,
            "type": "refresh",
            "jti": jti_id
        }
        access_token = self._token_encoder(access_payload)
        refresh_token = self._token_encoder(refresh_payload)

        jrs = JwtRedisStore()
        jrs.set_(_key=jti_id, value=time_now.isoformat())
        return access_token, refresh_token


    def _token_encoder(self, payload: dict[str, Any]):
        try:
            return jwt.encode(
                payload, key=self.secret_key, algorithm=self.algorithm
            )
        except JWTError:
            return None

        except Exception as ex:
            raise ex

    def _token_decoder(self, token: str | None) -> dict[str, Any] | None:
        if not token:
            return None

        try:
            return jwt.decode(token, key=self.secret_key, algorithms=[self.algorithm])

        except (JWTError, ExpiredSignatureError, JWTClaimsError):
            return None

    def _get_sub_in_access_cookie(self, request: Request) -> str | None:
        raw_token = request.cookies.get("access_token")
        if not raw_token:
            return None

        payload = self._token_decoder(raw_token)
        if payload and payload.get("type") == "access":
            jti_in_token = payload.get("jti")
            if not self.jti_memory.get_(jti_in_token):

                return None

            return payload.get("sub")

        return None

    def _get_sub_in_refresh_cookie(self, request: Request) -> str | None:
        raw_token = request.cookies.get("refresh_token")
        if not raw_token:
            return None

        payload = self._token_decoder(raw_token)
        if payload and payload.get("type") == "refresh":
            jti_in_token = payload.get("jti")
            if not self.jti_memory.get_(jti_in_token):

                return None

            return payload.get("sub")

        return None

    async def _verify_hash_password(self, password: str, hashed_password: str) -> bool:
        try:
            return await asyncio.to_thread(self.ph.verify, hashed_password, password)

        except (VerificationError, VerifyMismatchError, InvalidHashError):
            return False

    async def get_hash_password(self, password: str) -> str:
        return await asyncio.to_thread(self.ph.hash, password)

    def _set_cookie(self, user: str, resp: Response) -> str:
        access_token, refresh_token = self._generate_token(sub=user)
        resp.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="lax",
            secure=self.secure_cookie,
            max_age=access_age,
            path="/"
        )
        resp.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="strict",
            secure=self.secure_cookie,
            max_age=refresh_age,
            path="/"  ### DEVELOPMENT
        )
        return user

    def get_cookie_id(self, request: Request, response: Response) -> str | None:
        access_token = self._get_sub_in_access_cookie(request)
        if access_token:
            return access_token

        refresh_token = self._get_sub_in_refresh_cookie(request)
        if not refresh_token:
            return None

        return self._set_cookie(refresh_token, response)


    def revocation_of_jti(self, request: Request):
        raw_access_token = request.cookies.get("access_token")
        old_refresh_token = request.cookies.get("refresh_token")


        access_payload = self._token_decoder(raw_access_token)
        if access_payload and access_payload.get("type") == "access":
            jti_in_payload = access_payload.get("jti")
            self.jti_memory.delete_(jti_in_payload)
            return True

        refresh_payload = self._token_decoder(old_refresh_token)
        if refresh_payload and refresh_payload.get("type") == "refresh":
            jti_in_payload = refresh_payload.get("jti")
            self.jti_memory.delete_(jti_in_payload)
            return True

        return False


    def logout(self, response: Response) -> bool:
        try:
            response.set_cookie(
                key="access_token",
                value="",
                httponly=True,
                samesite="lax",
                secure=self.secure_cookie,
                max_age=0,
                path="/"
            )
            response.set_cookie(
                key="refresh_token",
                value="",
                httponly=True,
                samesite="strict",
                secure=self.secure_cookie,
                max_age=0,
                path="/"
            )
            return True
        except Exception as ex:
            raise HTTPException(status_code=400, detail=str(ex))

    async def login_with_cookie(self, user: str, password: str, hashed_password: str, resp: Response) -> bool:
        verified_password = await self._verify_hash_password(hashed_password=hashed_password, password=password)
        if not verified_password:
            return False

        self._set_cookie(user=user, resp=resp)
        return True

    def check_current_user_logged_in(self, request: Request):
        access_token = self._get_sub_in_access_cookie(request)
        if access_token:
            return True

        refresh_token = self._get_sub_in_refresh_cookie(request)
        if refresh_token:
            return True

        return False

class SecurityAuthOriginal:
    def __init__(self, is_development: bool = True):
        self._is_development = is_development

    @property
    def ph(self) -> PasswordHasher:
        global _ph
        if _ph is None:
            _ph = PasswordHasher()
        return _ph

    @property
    def secure_cookie(self):
        if self._is_development:
            return False
        return True

    def _token_generator(self, sub: str, token_type: str = "access_token") -> str:
        if token_type == "access_token":
            payload = self._get_access_encode(sub)
        elif token_type == "refresh_token":
            payload = self._get_refresh_encode(sub)
        else:
            payload = self._get_access_encode(sub)

        return jwt.encode(
            payload, key=settings.groq_api_key.get_secret_value(), algorithm="HS256"
        )

    @staticmethod
    def _get_access_encode(sub: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        return {
            "sub": sub,
            "exp": now + timedelta(minutes=5),
            "iat": now,
            "type": "access"
        }

    @staticmethod
    def _get_refresh_encode(sub: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        return {
            "sub": sub,
            "exp": now + timedelta(days=15),
            "iat": now,
            "type": "refresh"
        }

    @staticmethod
    def _token_decoder(token: str | None) -> dict[str, Any] | None:
        if not token:
            return None

        try:
            return jwt.decode(token, key=settings.groq_api_key.get_secret_value(), algorithms=["HS256"])

        except (JWTError, ExpiredSignatureError, JWTClaimsError):
            return None

    def _get_access_cookie_sub(self, request: Request) -> str | None:
        raw_token = request.cookies.get("access_token")
        if not raw_token:
            return None

        payload = self._token_decoder(raw_token)
        if payload and payload.get("type") == "access":
            user_id = payload["sub"]
            return user_id

        return None

    def _get_refresh_cookie_sub(self, request: Request) -> str | None:
        raw_token = request.cookies.get("refresh_token")
        if not raw_token:
            return None

        payload = self._token_decoder(raw_token)
        if payload and payload.get("type") == "refresh":
            user_id = payload["sub"]
            return user_id

        return None



    async def _verify_hash_password(self, password: str, hashed_password: str) -> bool:
        try:
            return await asyncio.to_thread(self.ph.verify, hashed_password, password)

        except (VerificationError, VerifyMismatchError, InvalidHashError):
            return False

    async def get_hash_password(self, password: str) -> str:
        return await asyncio.to_thread(self.ph.hash, password)

    def _set_cookie(self, user: str, resp: Response) -> str:
        access_token = self._token_generator(user, "access_token")
        refresh_token = self._token_generator(user, "refresh_token")
        resp.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="lax",
            secure=self.secure_cookie,
            max_age=access_age,
            path="/"
        )
        resp.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="strict",
            secure=self.secure_cookie,
            max_age=refresh_age,
            path="/" ### DEVELOPMENT
        )
        return user


    def get_cookie_id(self, request: Request, response: Response) -> str | None:
        access_token = self._get_access_cookie_sub(request)
        if access_token:
            return access_token

        refresh_token = self._get_refresh_cookie_sub(request)
        if not refresh_token:
            return None

        else:
            return self._set_cookie(refresh_token, response)

    def logout(self, request: Request, response: Response) -> bool:
        try:
            old_access = self._get_access_cookie_sub(request)
            old_refresh = self._get_refresh_cookie_sub(request)
            print(f"old_access: {old_access}, old_refresh: {old_refresh}")

            response.set_cookie(
                key="access_token",
                value="",
                httponly=True,
                samesite="lax",
                secure=self.secure_cookie,
                max_age=0,
                path="/"
            )
            response.set_cookie(
                key="refresh_token",
                value="",
                httponly=True,
                samesite="strict",
                secure=self.secure_cookie,
                max_age=0,
                path="/"
            )
            return True
        except Exception as ex:
            raise HTTPException(status_code=400, detail=str(ex))

    async def login_with_cookie(self, user: str, password: str, hashed_password: str, resp: Response) -> bool:
        verified_password = await self._verify_hash_password(password, hashed_password)
        if not verified_password:
            return False
        try:
            self._set_cookie(user, resp)
            return True
        except Exception:
            return False