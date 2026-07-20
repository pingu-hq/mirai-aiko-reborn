from fastapi import APIRouter, status, HTTPException, Depends
from app.services.auth.web_auth_service import HttpCookieManagerService
from app.dependencies.auth import (
    get_http_cookie_manager_service,
    get_user_login_service,
    get_user_create_service,
    get_user_id_from_cookie,
    get_login_state_service
)
from app.core.logger import app_logger
from app.services.auth.user_auth_services import AuthUserLoginService, AuthUserRegisterService, LoginStateService
from app.schemas.users import *

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)



@router.post("/login", status_code=status.HTTP_200_OK)
async def login_endpoint_v1(
        user: UserLoginV1,
        http_cookie: HttpCookieManagerService = Depends(get_http_cookie_manager_service),
        login_service: AuthUserLoginService = Depends(get_user_login_service),
        state: LoginStateService = Depends(get_login_state_service)
):
    try:
        sub_id = await login_service.get_id_for_token_from_login_v1(user=user)
        if not sub_id:
            app_logger.error(f"The User ({user.email}) password is incorrect")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized Error")

        if not await state.login_by_id(input_id=sub_id):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized Error")

        http_cookie.setting_http_cookie(sub=sub_id)
        app_logger.info(f"The User ({user.email}) has successfully logged in")
        return {"status": "Ok", "extra": user.email}
    except Exception as e:
        app_logger.error(f"User login error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized Error")


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup_endpoint_v1(
        user: UserRegisterV1,
        register_service: AuthUserRegisterService = Depends(get_user_create_service),
):
    try:
        is_registered = await register_service.signup_user_v1(user_register=user)
        if is_registered:
            return {"status": "Ok", "extra": user.email}

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request")
    except Exception as e:
        app_logger.error(f"User signup error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request")


@router.get("/me")
async def check_user_v1(user_id: str = Depends(get_user_id_from_cookie)):
    try:
        app_logger.info(f"The User ({user_id}) exists in the cookie")
        return {"test_user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"User check error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@router.delete("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_endpoint_v1(
        http_cookie: HttpCookieManagerService = Depends(get_http_cookie_manager_service),
        user_id: str = Depends(get_user_id_from_cookie),
        state: LoginStateService = Depends(get_login_state_service)
):
    http_cookie.deleting_id_from_http_cookie()
    await state.logout_by_id(input_id=user_id)
    app_logger.info("User logged out")