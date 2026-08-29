
from datetime import datetime, timedelta
from json import dumps as json_dumps
from json import loads as json_loads
from secrets import token_urlsafe
from typing import Literal

from fastapi import HTTPException, Request, Response, status
from redis.asyncio import Redis, RedisError

from app.core.config import settings
from app.repositories.caches import RedisCacheBaseRepository


class OpaqueTokenService:
    def __init__(self):
        self.redis_client: Redis = RedisCacheBaseRepository.get_redis_client()

    async def _set_value(self, key: str, value: bytes | str | dict[str, str],
        expire: timedelta | int
    ):
        if isinstance(value, dict):
            value = json_dumps(value)
        await self.redis_client.set(
            name=key,
            value=value,
            ex=expire
        )
        return True


    async def _get_value(self, key: str) -> dict[str, str] | None:
        value = await self.redis_client.get(name=key)
        if value is None:
            return None
        return json_loads(value)
        

    async def _delete_value(self, key: str) -> bool:
        try:
            await self.redis_client.delete(key)
            return True
        except RedisError:
            return False


    async def set_opaque_token(self, sub: str, token_type: Literal["access", "refresh"]) -> str | None:
        new_token: str = token_urlsafe(16)
        new_payload = {
            "token_type": f"{token_type}_token",
            "sub": sub,
            "iat": datetime.now(settings.ph_tz).strftime("%Y-%m-%d %H:%M:%S")
        }
        if token_type == "access":
            expire = timedelta(minutes=30)
        else:
            expire = timedelta(days=7)
        if await self._set_value(new_token, new_payload, expire):
            return new_token
        return None


    async def get_sub_from_opaque_token(self, token: str) -> tuple[str | None, str | None]:
        """Returns the sub and token type from the opaque token, if it exists."""
        value = await self._get_value(token)
        if value:
            current_sub = value.get("sub")
            token_type = value.get("token_type")
            if token_type in ["access_token", "refresh_token"] and current_sub:
                return current_sub, token_type
        return None, None

    async def delete_opaque_token(self, token: str) -> bool:
        """Deletes the opaque token from the cache."""
        return await self._delete_value(token)



class HttpCookieAuthService:
    def __init__(self,request: Request, response: Response):
        self.opaque_token_service = OpaqueTokenService()
        self.request = request
        self.response = response
        

    async def set_http_cookie(self, sub: str, token_type: Literal["access", "refresh"]):
        new_token = await self.opaque_token_service.set_opaque_token(sub, token_type)
        if new_token is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

        if settings.is_deployed_for_production:
            secure = True
        else:
            secure = False

        if token_type == "access":
            max_age = int(timedelta(minutes=7).total_seconds())
            same_site = "lax"
        else:
            max_age = int(timedelta(days=7).total_seconds())
            same_site = "strict"

        self.response.set_cookie(
            key=token_type,
            value=new_token,
            max_age=max_age,
            secure=secure,
            httponly=True,
            path="/",
            samesite=same_site,
        )
        
        return True

    def _get_token_from_cookie(self, token_type: Literal["access", "refresh"]) -> str | None:
        token = self.request.cookies.get(token_type, None)
        if token is None:
            return None
        return token

    async def _get_sub_from_access_token(self) -> str | None:
        old_token = self._get_token_from_cookie("access")
        if old_token is None:
            return None
        sub, token_type = await self.opaque_token_service.get_sub_from_opaque_token(token=old_token)
        if sub is None or token_type is None or token_type != "access_token":
            return None
        return sub

    async def _get_sub_from_refresh_token(self) -> str | None:
        old_token = self._get_token_from_cookie("refresh")
        if old_token is None:
            return None
        sub, token_type = await self.opaque_token_service.get_sub_from_opaque_token(token=old_token)
        if sub is None or token_type is None or token_type != "refresh_token":
            return None
        return sub

    async def get_user_id(self) -> str:
        sub_from_access = await self._get_sub_from_access_token()
        if sub_from_access:
            return sub_from_access
            
        sub_from_refresh = await self._get_sub_from_refresh_token()
        if sub_from_refresh is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is invalid")

        await self.opaque_token_service.delete_opaque_token(sub_from_refresh)
        await self.set_http_cookie(sub_from_refresh, "access")
        await self.set_http_cookie(sub_from_refresh, "refresh")
        return sub_from_refresh

    async def remove_http_cookie(self):
        old_access_token = self._get_token_from_cookie("access")
        if old_access_token:
            await self.opaque_token_service.delete_opaque_token(old_access_token)
            
        old_refresh_token = self._get_token_from_cookie("refresh")
        if old_refresh_token:
            await self.opaque_token_service.delete_opaque_token(old_refresh_token)
        
        self.response.delete_cookie("access")
        self.response.delete_cookie("refresh")
        return True

    async def is_user_still_logged_in(self) -> bool:
        return bool(await self._get_sub_from_access_token() or await self._get_sub_from_refresh_token())
