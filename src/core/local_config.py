from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from pydantic import SecretStr

env_file_path = Path(__file__).resolve().parent.parent.parent / "secrets" / ".env"

class Settings(BaseSettings):
    HELLO_WORLD: str = ""
    MONGO_DATABASE: SecretStr = "mongodb://localhost:27017"

    AZURE_API_KEY: SecretStr = None
    GROQ_API_KEY: SecretStr = None
    COHERE_API_KEY: SecretStr = None


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

    @property
    def groq_api_key(self):
        if not self.GROQ_API_KEY:
            self.value_error()
        return self.GROQ_API_KEY


    def cohere_api_key(self):
        if not self.COHERE_API_KEY:
            self.value_error()
        return self.COHERE_API_KEY

    model_config = SettingsConfigDict(
        env_file=env_file_path,
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()