from fastapi import APIRouter, status, HTTPException, Depends
from app.services.auth.opaque_auth_service import OpaqueAuthService
from app.dependencies.auth import (
    get_user_login_service,
    get_user_create_service,
    get_login_state_service,
get_opaque_auth_service
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
        state: LoginStateService = Depends(get_login_state_service),
        opaque_token: OpaqueAuthService = Depends(get_opaque_auth_service),
        login_service: AuthUserLoginService = Depends(get_user_login_service),
):
    try:
        sub_id = await login_service.get_id_for_token_from_login_v1(user=user)
        if not sub_id:
            app_logger.error(f"The User ({user.email}) password is incorrect")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized Error")

        if not await state.login_by_id(input_id=sub_id):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized Error")

        await opaque_token.login_user(sub_id)
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
async def check_user_v1(opaque_token: OpaqueAuthService = Depends(get_opaque_auth_service)):
    try:
        user_id = await opaque_token.get_user_id()
        access = opaque_token.get_raw_token_from_http_cookie("access")
        refresh = opaque_token.get_raw_token_from_http_cookie("refresh")
        app_logger.info(f"The User ({user_id}) exists in the cookie")
        return {"test_user_id": user_id, "extra": {"access":access, "refresh": refresh}}
    except HTTPException:
        raise
    except Exception as e:
        app_logger.error(f"User check error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@router.delete("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_endpoint_v1(
        opaque_token: OpaqueAuthService = Depends(get_opaque_auth_service),
        state: LoginStateService = Depends(get_login_state_service)
):
    user_id = await opaque_token.get_user_id()
    await opaque_token.logout_user()
    await state.logout_by_id(input_id=user_id)
    app_logger.info("User logged out")