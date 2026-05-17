from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from pydantic import SecretStr
from functools import lru_cache

env_file_path = Path(__file__).resolve().parent.parent.parent / "secrets" / ".env"

class Settings(BaseSettings):
    HELLO_WORLD: str = ""
    MONGO_DATABASE: SecretStr = "mongodb://localhost:27017"

    AZURE_API_KEY: SecretStr = None
    GROQ_API_KEY: SecretStr = None
    COHERE_API_KEY: SecretStr = None

    MILVUS_URI: SecretStr = None
    MILVUS_TOKEN: SecretStr = None

    AZURE_CLIENT_ID : SecretStr = None
    AZURE_TENANT_ID: SecretStr = None
    AZURE_CLIENT_SECRET: SecretStr = None
    AZURE_AI_PROJECT_ENDPOINT: SecretStr = None

    TEMP_FIRST_AGENT: SecretStr = None


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

    @property
    def cohere_api_key(self):
        if not self.COHERE_API_KEY:
            self.value_error()
        return self.COHERE_API_KEY

    @property
    def milvus_uri(self):
        if not self.MILVUS_URI:
            self.value_error()
        return self.MILVUS_URI

    @property
    def milvus_token(self):
        if not self.MILVUS_TOKEN:
            self.value_error()
        return self.MILVUS_TOKEN

    @property
    def client_id(self):
        if not self.AZURE_CLIENT_ID:
            self.value_error()
        return self.AZURE_CLIENT_ID

    @property
    def client_secret(self):
        if not self.AZURE_CLIENT_SECRET:
            self.value_error()
        return self.AZURE_CLIENT_SECRET

    @property
    def tenant_id(self):
        if not self.AZURE_TENANT_ID:
            self.value_error()
        return self.AZURE_TENANT_ID

    @property
    def ai_project_endpoint(self):
        if not self.AZURE_AI_PROJECT_ENDPOINT:
            self.value_error()
        return self.AZURE_AI_PROJECT_ENDPOINT

    @property
    def temp_first_agent(self):
        if not self.TEMP_FIRST_AGENT:
            self.value_error()
        return self.TEMP_FIRST_AGENT


    model_config = SettingsConfigDict(
        env_file=env_file_path,
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()