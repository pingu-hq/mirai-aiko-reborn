from fastapi import HTTPException, status
from app.services.auth.hash_password_service import AuthPasswordService
from app.repositories.no_sql_database.mongo_db_repository import UsersCollectionRepository
from app.schemas.users import UserRegisterV1, UserLoginV1
from app.core.logger import app_logger


class AuthUserLoginService:
    _email = "email"
    _external_id = "external_id"
    _password = "password"

    def __init__(
            self,
            auth_pass_service: AuthPasswordService,
            mongo_db: UsersCollectionRepository,
    ):
        self.mongo_db = mongo_db
        self.auth_pass_service = auth_pass_service

    def error_401(self, message: str, ex=None):
        log_details = f"Details: {message}"
        if ex:
            log_details += f" // Exception: {str(ex)}"
        app_logger.error(log_details)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    def error_500(self, message: str, ex=None):
        log_details = f"Details: {message}"
        if ex:
            log_details += f" // Exception: {str(ex)}"
        app_logger.error(log_details)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service Unavailable")



    async def login_user_to_get_id(self, user: UserLoginV1) -> str:
        try:
            user_data = await self.mongo_db.users.find_one({self._email: user.email})

            if user_data:
                hash_password = user_data.get(self._password)
                external_id = user_data.get(self._external_id)
                if external_id is None:
                    self.error_500("External id doesnt exist")

                hash_verify = await self.auth_pass_service.verify_hash_password(
                    hash_password=hash_password, password=user.password
                )
                if hash_verify:
                    return user_data.get(self._external_id)

                self.error_401(f"Verification for password of User({user.email} failed")

            self.error_401(message=f"User ({user.email}) cannot find the data in database")

        except Exception as ex:
            self.error_500("Unexpected error through login", ex=ex)


class AuthUserRegisterService:
    _external_id = "external_id"
    _password = "password"
    _date_created = "date_created"
    _email = "email"

    def __init__(
            self,
            auth_pass_service: AuthPasswordService,
            mongo_db: UsersCollectionRepository,
    ):
        self.mongo_db = mongo_db
        self.auth_pass_service = auth_pass_service


    async def hash_password(self, password: str):
        return await self.auth_pass_service.make_hash_password(password=password)

    async def safe_to_register_user(self, email: str):
        existing = await self.mongo_db.users.find_one({self._email: email})
        if existing:
            return False
        return True

    async def get_updated_form_v1(self, user: UserRegisterV1):
        hash_password = await self.hash_password(user.password)
        return user.to_mongo_db(hash_password=hash_password)

    async def signup_user_v1(self, user_register: UserRegisterV1):
        try:
            is_safe = await self.safe_to_register_user(email=user_register.email)
            if not is_safe:
                return False

            user_form = await self.get_updated_form_v1(user_register)
            await self.mongo_db.users.insert_one(user_form)
            return True
        except Exception as e:
            return False
