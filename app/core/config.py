import os
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv

load_dotenv()

class Settings:
    REDIS_URL: str | None = os.getenv("REDIS_URL", None)
    PH_TZ: ZoneInfo = ZoneInfo("Asia/Manila")
    IS_DEPLOYED_FOR_PRODUCTION: bool = os.getenv("IS_DEPLOYED_FOR_PRODUCTION", "false").lower() == "true"

    @property
    def redis_url(self) -> str:
        if not self.REDIS_URL:
            raise RuntimeError("REDIS_URL not set")
        return self.REDIS_URL

    @property
    def ph_tz(self) -> ZoneInfo:
        try:
            return self.PH_TZ
        except ZoneInfoNotFoundError:
            return ZoneInfo("Asia/Manila")

    @property
    def is_deployed_for_production(self) -> bool:
        return self.IS_DEPLOYED_FOR_PRODUCTION


settings = Settings()