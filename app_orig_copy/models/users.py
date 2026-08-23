from pydantic import BaseModel, Field
from datetime import datetime
from zoneinfo import ZoneInfo
import ulid


PH_TIMEZONE = ZoneInfo("Asia/Manila")
PH_TIME_FORMAT = "DATE: %B %d, %Y TIME: %I:%M:%S %p"
PH_MONGO_DB_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"


def date_created_default():
    return datetime.now(PH_TIMEZONE).strftime(PH_MONGO_DB_DATE_FORMAT)



class UserFormModel(BaseModel):
    email: str
    password: str = Field(min_length=8, description="Password for this user")
    date_created: str = Field(
        default_factory=lambda: date_created_default()
    )
    external_id: str = Field(
        default_factory=lambda: ulid.new().str
    )

    @property
    def to_mongo_dict(self):
        return self.model_dump()

    @property
    def get_mongo_dict(self):
        original_date_object = datetime.strptime(self.date_created, PH_MONGO_DB_DATE_FORMAT)
        new_date_created = original_date_object.strftime(PH_TIME_FORMAT)
        model_copy = self.model_dump().copy()
        model_copy["date_created"] = new_date_created
        return model_copy



