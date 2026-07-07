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





class UserLoginResponse(BaseModel):
    email: EmailStr = Field(..., description="User's email")

class UserCreateRequest(UserLoginResponse):
    password: str = Field(min_length=2, description="Password for this user")

class UserLoginRequestRequest(UserCreateRequest):
    date_created: datetime = Field(
        default_factory=_date_created
    )
    external_id: str = Field(default_factory=_new_ulid)


