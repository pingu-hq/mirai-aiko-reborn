from typing import Annotated

from fastapi import Depends, Request, Response

from app.dependencies.auth_dependency import HttpCookieAuthServiceDepends
from app.services.users_service import (
    UserLoginService,
    UserLogoutService,
    UserRegisterService,
    UserAccessService
)

type UserLogoutServiceDepends = Annotated[UserLogoutService, Depends(get_user_logout_service)]
type UserLoginServiceDepends = Annotated[UserLoginService, Depends(get_user_login_service)]
type UserRegisterServiceDepends = Annotated[UserRegisterService, Depends(get_user_register_service)]
type UserAccessServiceDepends = Annotated[UserAccessService, Depends(get_user_access_service)]


def get_user_login_service(
    http_cookie_auth_service: HttpCookieAuthServiceDepends,
) -> UserLoginService:
    return UserLoginService(http_cookie_auth_service)

def get_user_register_service() -> UserRegisterService:
    return UserRegisterService()


def get_user_logout_service(request: Request, response: Response) -> UserLogoutService:
    return UserLogoutService(request, response)


def get_user_access_service(request: Request, response: Response) -> UserAccessService:
    return UserAccessService(request, response)
