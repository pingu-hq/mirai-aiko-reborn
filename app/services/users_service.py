from datetime import datetime
from typing import Annotated

from fastapi import Depends, HTTPException, status
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.errors import DuplicateKeyError

from app.core.config import settings
from app.repositories.database import UsersRepository
from app.schemas.users_schema import UserLoginSchema, UserRegisterSchema
from app.services.http_cookie_service import (
    HttpCookieAuthService,
    get_http_cookie_auth_service,
)
from app.services.password_hasher_service import PasswordHasherService


class UserLoginService:
    def __init__(
        self,
        http_cookie_service: HttpCookieAuthService,
        user_repo: UsersRepository | None = None,
        password_hasher: PasswordHasherService | None = None,
    ):
        self.user_repo = user_repo or UsersRepository()
        self.password_hasher = password_hasher or PasswordHasherService()
        self.user_schema: UserLoginSchema | None = None
        self.http_cookie_service = http_cookie_service

    def insert_user_schema(self, user_schema: UserLoginSchema):
        self.user_schema = user_schema
        return self

    

    async def _get_user(self):
        if self.user_schema is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bad Request",
            )
        users_collection: AsyncCollection = await self.user_repo.get_users_collection()
        user_profile: dict | None = await users_collection.find_one(
            filter={"email": self.user_schema.email}
        )
        if user_profile is None:
            return None

        hashed_password_from_db = user_profile.get("password")
        if await self.password_hasher.verify_hash_password(
            hash_password=hashed_password_from_db,
            password=self.user_schema.password
        ):
            return user_profile.get("username")
        return None

    async def get_validated_username_from_db(self) -> str:
        user = await self._get_user()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized",
            )
        return user

    async def login_user_and_set_cookie(self):
        validated_user = await self.get_validated_username_from_db()
        if not validated_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized",
            )
        if await self.http_cookie_service.is_user_still_logged_in():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bad Request",
            )
        await self.http_cookie_service.set_http_cookie(sub=validated_user, token_type="access")
        await self.http_cookie_service.set_http_cookie(sub=validated_user, token_type="refresh")
        return True


def get_user_login_service(
    http_cookie_service: Annotated[HttpCookieAuthService, Depends(get_http_cookie_auth_service)]
) -> UserLoginService:
    return UserLoginService(http_cookie_service=http_cookie_service)

type UserLoginServiceDeps = Annotated[UserLoginService, Depends(get_user_login_service)]




    

class UserRegisterService:
    def __init__(
        self,
        user_repo: UsersRepository | None = None,
        password_hasher: PasswordHasherService | None = None,
    ):
        self.user_repo = user_repo or UsersRepository()
        self.user_schema: UserRegisterSchema | None = None
        self.password_hasher = password_hasher or PasswordHasherService()

    def insert_user_schema(self, user_schema: UserRegisterSchema):
        self.user_schema = user_schema

    async def register_user(self):
        if not self.user_schema:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request")
        
        users_collection: AsyncCollection = await self.user_repo.get_users_collection()
        hashed_password = await self.password_hasher.hash_password(
            password=self.user_schema.password
        )
        user_profile_data = {
            "email": self.user_schema.email,
            "username": self.user_schema.username,
            "password": hashed_password,
            "date_created": datetime.now(settings.ph_tz).strftime("%Y-%m-%d %H:%M:%S"),
        }
        try:
            await users_collection.insert_one(user_profile_data)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists",
            )

def get_user_register_service() -> UserRegisterService:
    return UserRegisterService()

type UserRegisterServiceDeps = Annotated[UserRegisterService, Depends(get_user_register_service)]