from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from pydantic import SecretStr

env_file_path = Path(__file__).resolve().parent.parent.parent / "secrets" / ".env"

class Settings(BaseSettings):
    HELLO_WORLD: str = ""
    AZURE_API_KEY: SecretStr = None
    MONGO_DATABASE: SecretStr = "mongodb://localhost:27017"

    model_config = SettingsConfigDict(
        env_file=env_file_path,
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @staticmethod
    def value_error():
        raise ValueError("No env file detected")

    @property
    def hello_world(self):
        if not self.HELLO_WORLD:
            self.value_error()
        return self.HELLO_WORLD

    @property
    def azure_api_key(self):
        if not self.AZURE_API_KEY:
            self.value_error()
        return self.AZURE_API_KEY

    @property
    def mongo_db(self):
        if not self.MONGO_DATABASE:
            self.value_error()
        return self.MONGO_DATABASE

settings = Settings()
print(settings.mongo_db.get_secret_value())