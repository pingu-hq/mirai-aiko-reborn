from app.repositories.in_memory_database.redis_repository import JtiCacheRepository, RedisAsyncRepository
from app.repositories.no_sql_database.mongo_db_repository import UsersCollectionRepository
from app.services.auth.hash_password_service import AuthPasswordService
from app.services.auth.web_auth_service import (
JwtTokenService,
JwtAndCookieHandlerService,
HttpCookieManagerService
)
from app.services.auth.user_auth_services import (
AuthUserLoginService,
AuthUserRegisterService,
LoginStateService
)
from app.services.auth.opaque_auth_service import OpaqueAuthService
from fastapi import Depends, Request, Response

def get_redis_async_repository() -> RedisAsyncRepository:
    return RedisAsyncRepository()


def get_redis_repository() -> JtiCacheRepository:
    return JtiCacheRepository()


def get_jwt_token_service(
        jti_repository: JtiCacheRepository = Depends(get_redis_repository)
) -> JwtTokenService:
    return JwtTokenService(jti_repository=jti_repository)


def get_jwt_and_cookie_handler_service(
        request: Request,
        response: Response,
) -> JwtAndCookieHandlerService:
    return JwtAndCookieHandlerService(
        request=request,
        response=response,
    )


def get_http_cookie_manager_service(
        jwt_service: JwtTokenService = Depends(get_jwt_token_service),
        auth_handler_service: JwtAndCookieHandlerService = Depends(get_jwt_and_cookie_handler_service)
) -> HttpCookieManagerService:
    return HttpCookieManagerService(
        jwt_service=jwt_service,
        auth_handler_service=auth_handler_service
    )


def get_user_collection_repository() -> UsersCollectionRepository:
    return UsersCollectionRepository()


def get_auth_password_service() -> AuthPasswordService:
    return AuthPasswordService()


def get_user_login_service(
        auth_pass_service: AuthPasswordService = Depends(get_auth_password_service),
        mongo_db: UsersCollectionRepository = Depends(get_user_collection_repository)
):
    return AuthUserLoginService(
        auth_pass_service=auth_pass_service,
        mongo_db=mongo_db
    )

def get_user_create_service(
        auth_pass_service: AuthPasswordService = Depends(get_auth_password_service),
        mongo_db: UsersCollectionRepository = Depends(get_user_collection_repository)
):
    return AuthUserRegisterService(
        auth_pass_service=auth_pass_service,
        mongo_db=mongo_db
    )

def get_user_id_from_cookie(
        cookie_service: HttpCookieManagerService = Depends(get_http_cookie_manager_service)
) -> str:
    return cookie_service.get_existing_user_id_from_cookie()


def get_login_state_service() -> LoginStateService:
    return LoginStateService()

def get_opaque_auth_service(
        request: Request, response: Response,
        redis_async_repository: RedisAsyncRepository = Depends(get_redis_async_repository),
) -> OpaqueAuthService:
    return OpaqueAuthService(
        request=request, response=response,
        redis_repository=redis_async_repository,
    )