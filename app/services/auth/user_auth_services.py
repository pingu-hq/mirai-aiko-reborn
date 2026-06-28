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
