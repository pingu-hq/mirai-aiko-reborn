from app.repositories.in_memory_database.redis_repository import JtiCacheRepository
from app.core.local_config import settings
from datetime import datetime, timezone, timedelta
from typing import Any, Literal
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
from fastapi import Request, Response
from json import (
    dumps as json_dumps,
    loads as json_loads
)
import ulid



IS_IN_TESTING_PHASE = True


class JwtTokenService:
    def __init__(self, jti_repository: JtiCacheRepository | None = None):
        self.jti_cache = jti_repository


    @staticmethod
    def create_payload(sub: Any, token_type: Literal["access", "refresh"], jti: str | None = None) -> dict:
        current_time = datetime.now(timezone.utc)
        if token_type == "access":
            expire_time = current_time + timedelta(seconds=10)
        else:
            expire_time = current_time + timedelta(days=15)

        payload = {
            "sub": str(sub),
            "exp": expire_time,
            "iat": current_time,
            "type": token_type,
        }
        if jti:
            payload["jti"] = jti
        return payload

    @staticmethod
    def token_encoder(payload: dict[str, Any], secret_key: str):
        try:
            return jwt.encode(payload, key=secret_key)
        except JWTError:
            return None
        except Exception as ex:
            raise ex

    @staticmethod
    def token_decoder(token: str | None, secret_key: str) -> dict[str, Any] | None:
        if not token:
            return None

        try:
            return jwt.decode(token, key=secret_key, algorithms=["HS256"])

        except (JWTError, ExpiredSignatureError, JWTClaimsError):
            return None

    def create_jti(self, sub):
        if self.jti_cache is None:
            raise ConnectionError("No redis client injected")

        if not isinstance(sub, str):
            sub = str(sub)

        jti_key = ulid.new().str
        current_datetime = datetime.now(timezone.utc)
        raw_jti_value = {
            "date_created": current_datetime.isoformat(),
            "valid_date_until": (current_datetime + timedelta(days=15)).isoformat(),
            "reference_id": sub,
        }
        jti_value = json_dumps(raw_jti_value)
        self.jti_cache.set_value(
            name=jti_key, value=jti_value, time=timedelta(days=15)
        )
        return jti_key

    def read_jti(self, jti_key):
        if self.jti_cache is None:
            raise ConnectionError("No redis client injected")

        raw_value = self.jti_cache.get_value(jti_key)
        if not raw_value:
            return None

        return json_loads(raw_value)

    def delete_jti(self, jti_key):
        if self.jti_cache is None:
            raise ConnectionError("No redis client injected")
        self.jti_cache.delete(jti_key)


class JwtAndCookieHandlerService:
    def __init__(self, request: Request, response: Response):
        self.req = request
        self.resp = response
        self.access_key = "access_token"
        self.refresh_key = "refresh_token"

    @property
    def secure_cookie(self):
        if IS_IN_TESTING_PHASE:
            return False

        return True

    @staticmethod
    def max_age(token_type: str) -> int:
        if token_type == "access_token":
            return int(timedelta(minutes=5).total_seconds())

        elif token_type == "refresh_token":
            return int(timedelta(days=15).total_seconds())

        else:
            return int(timedelta(minutes=5).total_seconds())

    def set_access_cookies(self, token: str):
        self.internal_setup_cookie(
            token_value=token,
            key=self.access_key,
            same_site="lax",
            max_age=self.max_age(self.access_key)
        )

    def set_refresh_cookies(self, token: str):
        self.internal_setup_cookie(
            key=self.refresh_key,
            token_value=token,
            same_site="strict",
            max_age=self.max_age(self.refresh_key)
        )

    def internal_setup_cookie(self, key, token_value, max_age, same_site):
        self.resp.set_cookie(
            key=key,
            value=token_value,
            httponly=True,
            samesite=same_site,
            secure=self.secure_cookie,
            max_age=max_age,
            path="/"
        )

    def get_raw_access_cookies(self):
        return self.req.cookies.get(self.access_key)

    def get_raw_refresh_cookies(self):
        return self.req.cookies.get(self.refresh_key)

    def get_raw_jwt_access_token_from_cookie(self):
        return self.req.cookies.get(self.access_key)

    def get_raw_jwt_refresh_token_from_cookie(self):
        return self.req.cookies.get(self.refresh_key)




class HttpCookieManagerService:
    def __init__(self, jwt_service: JwtTokenService, auth_handler_service: JwtAndCookieHandlerService):
        self.jwt_service = jwt_service
        self.auth_handler_service = auth_handler_service
        self.secret_key = settings.jwt_secret_key

    def setting_http_cookie(self, sub: str):
        new_jti = self.jwt_service.create_jti(sub=sub)

        new_access_payload = self.jwt_service.create_payload(
            sub=sub,
            token_type="access",
            jti=new_jti
        )
        new_refresh_payload = self.jwt_service.create_payload(
            sub=sub,
            token_type="refresh",
            jti=new_jti
        )
        new_access_token = self.jwt_service.token_encoder(
            payload=new_access_payload,
            secret_key=self.secret_key.get_secret_value()
        )
        new_refresh_token = self.jwt_service.token_encoder(
            payload=new_refresh_payload,
            secret_key=self.secret_key.get_secret_value()
        )
        if not new_access_token or not new_refresh_token:
            return None

        self.auth_handler_service.set_access_cookies(token=new_access_token)
        self.auth_handler_service.set_refresh_cookies(token=new_refresh_token)

        return new_jti

    def deleting_id_from_http_cookie(self):
        _, jti = self._get_refresh_sub_and_jti()
        self.jwt_service.delete_jti(jti_key=jti)


    def getting_id_from_http_cookie(self):
        access_id, access_jti = self._get_access_sub_and_jti()
        if access_id and access_jti:
            return access_id

        refresh_id, refresh_jti = self._get_refresh_sub_and_jti()
        if refresh_id and refresh_jti:

            self.jwt_service.delete_jti(refresh_jti)
            http_cookie = self.setting_http_cookie(sub=refresh_id)
            if not http_cookie:
                return None
            return refresh_id
        return None

    def getting_id_from_http_cookie_with_jti(self):
        access_id, access_jti = self._get_access_sub_and_jti()
        if access_id and access_jti:
            return access_id, access_jti

        refresh_id, refresh_jti = self._get_refresh_sub_and_jti()
        if refresh_id and refresh_jti:

            self.jwt_service.delete_jti(refresh_jti)
            http_cookie = self.setting_http_cookie(sub=refresh_id)
            if not http_cookie:
                return "External id not exist or logged out", "Jti expired or not exist"

            return refresh_id, refresh_jti
        return "Error for external id", "Jti is not processed due to external id"

    def test_get_jti_from_http_cookie(self):
        _, jti_access = self._get_access_sub_and_jti()
        _, jti_refresh = self._get_refresh_sub_and_jti()
        if not jti_access:
            jti_access = "Jti access is expired or not exist"

        if not jti_refresh:
            jti_refresh = "Jti refresh is expired or not exist"

        return jti_access, jti_refresh


    def _get_access_sub_and_jti(self):
        raw_jwt = self.auth_handler_service.get_raw_jwt_access_token_from_cookie()
        payload = self.jwt_service.token_decoder(raw_jwt, secret_key=self.secret_key.get_secret_value())

        if not payload:
            return None, None

        if payload.get("type") != "access":
            return None, None

        jti_key = payload.get("jti")

        sub = payload.get("sub")

        jti_exist = self.jwt_service.read_jti(jti_key=jti_key)

        if jti_exist:
            return sub, jti_key

        return sub, None

    def _get_refresh_sub_and_jti(self):
        raw_jwt = self.auth_handler_service.get_raw_jwt_refresh_token_from_cookie()
        payload = self.jwt_service.token_decoder(raw_jwt, secret_key=self.secret_key.get_secret_value())

        if not payload:
            return None, None

        if payload.get("type") != "refresh":
            return None, None

        jti_key = payload.get("jti")

        sub = payload.get("sub")

        jti_exist = self.jwt_service.read_jti(jti_key=jti_key)

        if jti_exist:
            return sub, jti_key

        return sub, None