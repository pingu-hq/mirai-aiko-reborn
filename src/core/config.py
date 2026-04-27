from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def _env_file_name(name: str):
    return BASE_DIR / "secret_keys" / f".env.{name}"

class LocalConfig(BaseSettings):
    SECRET_KEY: SecretStr = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5
    REFRESH_TOKEN_EXPIRE_DAYS: int = 15
    ALGORITHM: str = "HS256"


    model_config = SettingsConfigDict(
        env_file=_env_file_name("local"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def secret_key(self) -> SecretStr:
        if not self.SECRET_KEY:
            raise ValueError("No secret key provided")
        return self.SECRET_KEY

    @property
    def access_token_minutes(self):
        return self.ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def refresh_token_days(self):
        return self.REFRESH_TOKEN_EXPIRE_DAYS

    @property
    def algorithm(self):
        return self.ALGORITHM

local_config = LocalConfig()
