from app.services.auth.hash_password_service import AuthPasswordService
from app.repositories.no_sql_database.mongo_db_repository import UsersCollectionRepository
from app.models.users import UserFormModel
from app.core.logger import app_logger
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import ulid


class UserAuthenticationService:
    def __init__(self,
            auth_pass_service: AuthPasswordService,
            mongo_db: UsersCollectionRepository,
    ):
        self.mongo_db = mongo_db
        self.auth_pass_service = auth_pass_service

    async def login_user(self, email, password):
        form = await self.mongo_db.users.find_one({"email": email})
        if not form:
            return None
        
        hash_password = form.get("password")
        is_valid = await self.auth_pass_service.verify_hash_password(
            password=password, hash_password=hash_password
        )
        if not is_valid:
            return None

        return form.get("external_id")



    async def sign_up_user(self, email, password):
        try:
            hashed_pass = await self.auth_pass_service.make_hash_password(password=password)

            form = UserFormModel(
                email=email,
                password=hashed_pass
            )
            await self.mongo_db.users.insert_one(form.get_mongo_dict)
            app_logger.info(f"eID:{form.external_id} has been successfully registered")
            return form.external_id
        except Exception as e:
            app_logger.error(f"Login user {email} failed. Error: {e}")
            raise e

    async def login_user_v1(self, email, password):
        try:
            form = await self.mongo_db.users.find_one({"email": email})
            if not form:
                return None

            hash_password = form.get("password")
            is_valid = await self.auth_pass_service.verify_hash_password(
                password=password, hash_password=hash_password
            )
            if not is_valid:
                return None
            ph_tz = ZoneInfo("Asia/Manila")
            login_time = datetime.now(ph_tz)

            return {
                "email": form["email"],
                "external_id": form["external_id"],
                "login_time": login_time
            }
        except Exception as e:
            app_logger.error(f"Login user {email} failed. Error: {e}")
            return None


class AuthUserLoginService:
    _external_id = "external_id"
    _password = "password"
    _date_created = "date_created"

    def __init__(
            self,
            auth_pass_service: AuthPasswordService,
            mongo_db: UsersCollectionRepository,
    ):
        self.mongo_db = mongo_db
        self.auth_pass_service = auth_pass_service
        self.document_state = None
        self.email_as_key = None

    async def insert_email(self, email):
        try:
            self.email_as_key = email
            self.document_state = await self.mongo_db.users.find_one({"email": email})
            if self.document_state is None:
                return False
            return True
        except Exception as e:
            self.document_state = None
            self.email_as_key = None
            return False

    @staticmethod
    def state_error():
        raise Exception("State is None. Please insert email through insert_email function")

    def internal_get_state(self, key):
        if self.document_state is None:
            raise self.state_error()
        value = self.document_state.get(key)
        if not value:
            return None
        return value


    def get_external_id(self):
        return self.internal_get_state(self._external_id)

    def get_password(self):
        return self.internal_get_state(self._password)

    def get_date_created(self):
        return self.internal_get_state(self._date_created)

    async def verify_password(self, password):
        current_hashed_password = self.document_state.get("password")
        is_valid = await self.auth_pass_service.verify_hash_password(
            password=password, hash_password=current_hashed_password
        )
        if not is_valid:
            return False
        return True