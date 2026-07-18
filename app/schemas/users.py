from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from zoneinfo import ZoneInfo
from functools import lru_cache
import ulid


@lru_cache(maxsize=1)
def _get_ph_timezone() -> ZoneInfo:
    return ZoneInfo("Asia/Manila")

def _new_ulid():
    return ulid.new().str

def _date_created():
    return datetime.now(_get_ph_timezone())



class UserLoginV1(BaseModel):
    email: str = Field(..., description="User's email")
    password: str = Field(min_length=2, description="Password for this user")


class UserRegisterV1(BaseModel):
    email: str = Field(..., description="User's email")
    password: str = Field(min_length=2, description="Password for this user")
    date_created: datetime = Field(default_factory=_date_created, exclude=True, init=False)
    external_id: str = Field(default_factory=_new_ulid, exclude=True, init=False)