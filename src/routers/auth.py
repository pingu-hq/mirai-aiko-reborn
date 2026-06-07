from fastapi import APIRouter, Response, Request, status, HTTPException, Depends
from pydantic import BaseModel
from services.auth.web_auth_service import (
    JwtTokenService,
    HttpCookieManagerService,
    JwtAndCookieHandlerService
)
from services.auth.user_auth_services import UserAuthenticationService
from services.auth.hash_password_service import AuthPasswordService
from repositories.no_sql_database.mongo_db_repository import UsersCollectionRepository
from repositories.in_memory_database.redis_repository import JtiCacheRepository


def get_jti_repo() -> JtiCacheRepository:
    return JtiCacheRepository()


def get_jwt_service(jti_repo: JtiCacheRepository = Depends(get_jti_repo)) -> JwtTokenService:
    return JwtTokenService(jti_repo)


def get_pass_service() -> AuthPasswordService:
    return AuthPasswordService()


def get_user_mongo_db() -> UsersCollectionRepository:
    return UsersCollectionRepository()


def get_user_auth_service(
        pass_service: AuthPasswordService = Depends(get_pass_service),
        user_mongo_db: UsersCollectionRepository = Depends(get_user_mongo_db)
) -> UserAuthenticationService:
    return UserAuthenticationService(
        pass_service, user_mongo_db
    )


def get_jwt_and_cookie_handler_service(
        request: Request,
        response: Response,
):
    return JwtAndCookieHandlerService(request, response)


def get_http_cookie_service(
        handler_service: JwtAndCookieHandlerService = Depends(get_jwt_and_cookie_handler_service),
        jwt_service: JwtTokenService = Depends(get_jwt_service),
):
    return HttpCookieManagerService(
        jwt_service=jwt_service, auth_handler_service=handler_service
    )


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
        http_cookie: HttpCookieManagerService = Depends(get_http_cookie_service),
        user_auth_service: UserAuthenticationService = Depends(get_user_auth_service),
):
    try:
        user_account = await user_auth_service.login_user(
            email=user.email,
            password=user.password
        )
        if not http_cookie.setting_http_cookie(sub=user_account):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        return UserRead(external_id=user_account)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup_endpoint_v1(
        user: User,
        user_auth_service: UserAuthenticationService = Depends(get_user_auth_service)
):
    try:
        user_account = await user_auth_service.sign_up_user(
            email=user.email,
            password=user.password
        )
        return UserRead(external_id=user_account)
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@router.get("/me")
async def check_user_v1(
        http_cookie: HttpCookieManagerService = Depends(get_http_cookie_service),

):
    try:
        external_id, jti = http_cookie.getting_id_from_http_cookie_with_jti()
        if not external_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return {
            "external_id": external_id,
            "jti_key": jti,
        }
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@router.delete("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_endpoint_v1(
        http_cookie: HttpCookieManagerService = Depends(get_http_cookie_service),
):
    http_cookie.deleting_id_from_http_cookie()