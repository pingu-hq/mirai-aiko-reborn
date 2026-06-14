from fastapi import APIRouter, status, HTTPException, Depends
from pydantic import BaseModel
from app.services.auth.web_auth_service import HttpCookieManagerService
from app.services.auth.user_auth_services import UserAuthenticationService
from app.dependencies.auth import get_http_cookie_manager_service, get_user_authentication_service
from app.core.logger import app_logger





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
        user_account = await user_auth_service.login_user(
            email=user.email,
            password=user.password
        )
        if not http_cookie.setting_http_cookie(sub=user_account):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

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