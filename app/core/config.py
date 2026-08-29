import os
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGO_URI: str | None = os.getenv("MONGO_URI", None)
    REDIS_URI: str | None = os.getenv("REDIS_URI", None)
    PH_TZ: ZoneInfo = ZoneInfo("Asia/Manila")
    IS_DEPLOYED_FOR_PRODUCTION: bool = os.getenv("IS_DEPLOYED_FOR_PRODUCTION", "false").lower() == "true"
    GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY", None)
    COHERE_API_KEY: str | None = os.getenv("COHERE_API_KEY", None)
    MILVUS_URI: str | None = os.getenv("MILVUS_URI", None)
    MILVUS_TOKEN: str | None = os.getenv("MILVUS_TOKEN", None)
    

    @property
    def ph_tz(self) -> ZoneInfo:
        try:
            return self.PH_TZ
        except ZoneInfoNotFoundError:
            return ZoneInfo("Asia/Manila")

    @property
    def is_deployed_for_production(self) -> bool:
        return self.IS_DEPLOYED_FOR_PRODUCTION


    @property
    def mongo_uri(self) -> str:
        if not self.MONGO_URI:
            raise RuntimeError("MONGO_URI not set")
        return self.MONGO_URI

    @property
    def redis_uri(self) -> str:
        if not self.REDIS_URI:
            raise RuntimeError("REDIS_URI not set")
        return self.REDIS_URI

    @property
    def groq_api_key(self) -> str:
        if not self.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY not set")
        return self.GROQ_API_KEY

    @property
    def cohere_api_key(self) -> str:
        if not self.COHERE_API_KEY:
            raise RuntimeError("COHERE_API_KEY not set")
        return self.COHERE_API_KEY

    @property
    def milvus_uri(self) -> str:
        if not self.MILVUS_URI:
            raise RuntimeError("MILVUS_URI not set")
        return self.MILVUS_URI

    @property
    def milvus_token(self) -> str:
        if not self.MILVUS_TOKEN:
            raise RuntimeError("MILVUS_TOKEN not set")
        return self.MILVUS_TOKEN


settings = Settings()