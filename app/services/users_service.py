from datetime import datetime

from fastapi import HTTPException, status
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.errors import DuplicateKeyError

from app.core.config import settings
from app.repositories.database import UsersRepository
from app.schemas.users_schema import UserLoginSchema, UserRegisterSchema
from app.services.password_hasher_service import PasswordHasherService


class UserLoginService:
    def __init__(
        self,
        user_schema: UserLoginSchema,
        user_repo: UsersRepository | None = None,
        password_hasher: PasswordHasherService | None = None,
    ):
        self.user_repo = user_repo or UsersRepository()
        self.password_hasher = password_hasher or PasswordHasherService()
        self.user_schema = user_schema

    async def _get_user(self):
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

    async def get_user(self) -> str:
        user = await self._get_user()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized",
            )
        return user


class UserRegisterService:
    def __init__(
        self,
        user_schema: UserRegisterSchema,
        user_repo: UsersRepository | None = None,
        password_hasher: PasswordHasherService | None = None,
    ):
        self.user_repo = user_repo or UsersRepository()
        self.user_schema = user_schema
        self.password_hasher = password_hasher or PasswordHasherService()

    async def register_user(self):
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