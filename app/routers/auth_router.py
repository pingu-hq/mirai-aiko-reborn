from secrets import token_urlsafe

from fastapi import APIRouter, status

from app.dependencies.users_dependency import (
    UserAccessServiceDepends,
    UserLoginServiceDepends,
    UserLogoutServiceDepends,
    UserRegisterServiceDepends,
)
from app.schemas.users_schema import UserLoginSchema, UserRegisterSchema

router = APIRouter()


SAMPLE_USER: dict[str, str] | None = None


def random_user() -> dict[str, str]:
    return {
        "email": f"{token_urlsafe(8)}@yahoo.com",
        "username": token_urlsafe(8),
        "password": token_urlsafe(8),
    }

@router.get("/sample-user-for-testing")
def get_sample_user():
    global SAMPLE_USER
    if SAMPLE_USER is None:
        SAMPLE_USER = random_user()
    return SAMPLE_USER


@router.post("/register-user", status_code=status.HTTP_201_CREATED)
async def register_user(user_schema: UserRegisterSchema, user_register_service: UserRegisterServiceDepends):
    user_register_service.insert_user_schema(user_schema)
    await user_register_service.register_user()
    return {"message": "User registered successfully"}


@router.post("/login-user", status_code=status.HTTP_200_OK)
async def login_user(user_login_schema: UserLoginSchema, user_login_service: UserLoginServiceDepends):
    user_login_service.insert_user_schema(user_login_schema)
    await user_login_service.login_user_and_set_cookie()
    return {"message": "User logged in successfully"}


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_me(user_access_service: UserAccessServiceDepends):
    sub = await user_access_service.get_user_id()
    return {"message": "User logged in successfully", "sub": sub}


@router.get("/logout", status_code=status.HTTP_200_OK)
async def logout(logout_service: UserLogoutServiceDepends):
    if await logout_service.logout_and_clear_cookies():
        return {"message": "User logged out successfully"}
    return {"message": "No active session to logout"}
