from typing import Any

from fastapi import APIRouter, status, HTTPException, Depends, Request, Response
from pydantic import BaseModel
from app.services.auth.web_auth_service import HttpCookieManagerService
from app.services.auth.user_auth_services import UserAuthenticationService
from app.dependencies.auth import get_http_cookie_manager_service, get_user_authentication_service
from app.core.logger import app_logger
from app.core.local_config import settings



from cachetools import TTLCache
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
import ulid
import json





def ttl_cache_object():
    if not hasattr(ttl_cache_object, "ttl"):
        ttl_cache_object.ttl = TTLCache(maxsize=100, ttl=300)
    return ttl_cache_object.ttl


def set_ttl_cache(user_id: str, value):
    ttl_cache = ttl_cache_object()
    ttl_cache[user_id] = value
    return ttl_cache[user_id]

def set_ttl_cache_with_specific_value(
        token: str,
        user_id: str, current_time: datetime,
):
    ttl_cache = ttl_cache_object()
    payload = {
        "sub": user_id,
        "iat": current_time,
        "type": "access"
    }
    ttl_cache[token] = payload
    return ttl_cache[token]


def get_ttl_cache(user_id: str) -> dict[str, Any] | None:
    ttl_cache = ttl_cache_object()
    if user_id in ttl_cache:
        return ttl_cache[user_id]
    ttl_cache.expire()
    return None


def create_jwt_refresh_token(user_id: str, jti: str | None = None):
    try:
        ph_tz = ZoneInfo("Asia/Manila")
        current_time = datetime.now(ph_tz)
        payload = {
            "sub": user_id,
            "iat": current_time,
            "exp": current_time + timedelta(days=15),
            "type": "refresh",
        }

        if jti:
            payload["jti"] = jti

        return jwt.encode(payload, key=settings.jwt_secret_key)

    except JWTError:
        return None
    except Exception as ex:
        raise ex

def create_opaque_access_token(user_id: str):
    ph_tz = ZoneInfo("Asia/Manila")
    current_time = datetime.now(ph_tz)
    new_token = ulid.new().str
    set_ttl_cache_with_specific_value(
        user_id=user_id, token=new_token, current_time=current_time
    )
    return new_token


def get_jwt_payload(token: str):
    try:
        return jwt.decode(token=token, key=settings.jwt_secret_key, algorithms=["HS256"])
    except (JWTError, ExpiredSignatureError, JWTClaimsError):
        return None

def set_access_cookie(token: str,  response: Response):

    if settings.project_development_mode:
        secure = False
    else:
        secure = True
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=int(timedelta(minutes=5).total_seconds()),
        secure=secure,
        path="/"
    )

def set_refresh_cookie(token: str, response: Response):
    if settings.project_development_mode:
        secure = False
    else:
        secure = True
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        samesite="strict",
        max_age=int(timedelta(days=15).total_seconds()),
        secure=secure,
        path="/"
    )

def get_raw_refresh_cookie(request: Request):
    return request.cookies.get("refresh_token")

def get_raw_access_cookie(request: Request):
    return request.cookies.get("access_token")

def get_access_payload_from_cookie(request: Request):
    memory_cache_id = get_raw_access_cookie(request)
    if not memory_cache_id:
        return None
    payload = get_ttl_cache(memory_cache_id)
    if not payload:
        return None
    return payload



def get_refresh_payload_from_cookie(request: Request):
    raw_token = get_raw_refresh_cookie(request)
    if not raw_token:
        return None
    decoded_payload = get_jwt_payload(token=raw_token)
    if not decoded_payload:
        return None
    return decoded_payload


# def get_id_from_cookie(request: Request, response: Response):
#     access_payload = get_access_payload_from_cookie(request)
#     if access_payload:
#         return access_payload.get("sub")
#
#     refresh_payload = get_refresh_payload_from_cookie(request=request)
#     if not refresh_payload:
#         return None
#
#     if refresh_payload and refresh_payload.get("type") == "refresh":
#         refresh_token
#         create_opaque_access_token()

class AccessTokenService:
    ph_tz = ZoneInfo("Asia/Manila")
    def __init__(self, request: Request, response: Response):
        self.request = request
        self.response = response

    @property
    def ttl_cache(self):
        return ttl_cache_object()

    def create_token(self, user_id: str):
        new_token = ulid.new().str
        new_payload = {
            "sub": user_id,
            "iat": datetime.now(self.ph_tz),
            "type": "access",
        }
        # if user_id not in self.ttl_cache:
        #     self.ttl_cache[new_token] = new_payload
        #     return new_token
        # return None
        final_payload = json.dumps(new_payload)
        self.ttl_cache[new_token] = final_payload
        return final_payload

    def get_payload_by_token(self, token: str) -> dict[str, Any] | None:
        if token in self.ttl_cache:
            return self.ttl_cache[token]
        self.ttl_cache.expire()
        return None

    def set_cookie(self, user_id: str):
        new_token = self.create_token(user_id=user_id)
        if settings.project_development_mode:
            secure = False
        else:
            secure = True
        self.response.set_cookie(
            key="access_token",
            value=new_token,
            httponly=True,
            samesite="lax",
            max_age=int(timedelta(minutes=5).total_seconds()),
            secure=secure,
            path="/"
        )
        return True

    def get_cookie(self):
        old_opaque_token = self.request.cookies.get("access_token")
        if not old_opaque_token:
            return None

        raw_payload = self.get_payload_by_token(token=old_opaque_token)
        if not raw_payload:
            return None

        old_payload = json.loads(raw_payload)

        return old_payload.get("sub")


















router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)


class User(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    external_id: str


@router.post("/login", status_code=status.HTTP_200_OK)
async def login_endpoint_v1(
        user: User,
        http_cookie: HttpCookieManagerService = Depends(get_http_cookie_manager_service),
        user_auth_service: UserAuthenticationService = Depends(get_user_authentication_service),
):
    try:
        user_account = await user_auth_service.login_user_v1(
            email=user.email,
            password=user.password
        )
        external_id = user_account.get("external_id")
        if not user_account:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        set_ttl_cache(user_id=external_id, value=user_account)

        # http_cookie.setting_http_cookie(sub=external_id)

        app_logger.info(f"The User ({user.email}) has successfully logged in")
        return UserRead(external_id=user_account)
    except Exception as e:
        app_logger.error(f"User login error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized Error")


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup_endpoint_v1(
        user: User,
        user_auth_service: UserAuthenticationService = Depends(get_http_cookie_manager_service)
):
    try:
        user_account = await user_auth_service.sign_up_user(
            email=user.email,
            password=user.password
        )
        return UserRead(external_id=user_account)
    except Exception as e:
        app_logger.error(f"User signup error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request")


@router.get("/me")
async def check_user_v1(
        http_cookie: HttpCookieManagerService = Depends(get_http_cookie_manager_service),

):
    try:
        external_id, jti = http_cookie.getting_id_from_http_cookie_with_jti()
        if not external_id:
            app_logger.error(f"User check error: User ({external_id})")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        app_logger.info(f"The User ({external_id}) has successfully logged in")
        return {
            "external_id": external_id,
            "jti_key": jti,
        }
    except Exception as e:
        app_logger.error(f"User check error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@router.delete("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_endpoint_v1(
        http_cookie: HttpCookieManagerService = Depends(get_http_cookie_manager_service),
):
    http_cookie.deleting_id_from_http_cookie()
    app_logger.info("User logged out")