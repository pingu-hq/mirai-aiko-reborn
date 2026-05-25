from typing import Any
from fastapi import HTTPException, status
from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel, ConfigDict, PrivateAttr
from core.local_config import settings
from fastapi import Request
from dotenv import load_dotenv
from pathlib import Path
from abc import ABC, abstractmethod
import os

load_dotenv(Path(__file__).parent.parent.parent.resolve(True) / "secrets" / "llm_config.txt")

def load_azure_client():
    params = {
        "base_url" : settings.azure_endpoint.get_secret_value(),
        "api_key" : settings.azure_api_key.get_secret_value()
    }
    client_async = AsyncOpenAI(**params)
    client_sync = OpenAI(**params)

    return client_async, client_sync



def lifespan_context_azure_llm():
    return load_azure_client()



class LLMBase(ABC, BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    request: Request | None
    content: str | list[dict[str, str]]
    model_type: str


    @property
    def _llm(self):
        if self.request is None:
            return lifespan_context_azure_llm()[1]
        return self.request.app.state.azure_llm[1]

    @property
    def _llm_async(self):
        if self.request is None:
            return lifespan_context_azure_llm()[0]
        return self.request.app.state.azure_llm[0]

    @property
    def _message_content(self):
        return self._internal_content_to_message(self.content)

    @property
    def _model(self):
        try:
            return os.environ[self.model_type]
        except KeyError:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")


    @staticmethod
    def _internal_content_to_message(content: str | list[dict]) -> list[Any | dict[str, Any | str]]:
        if isinstance(content, str):
            return [{"role": "user", "content": content}]

        allowed_roles = ["user", "system"]
        if isinstance(content, list):
            if content[0].get("role") in allowed_roles:
                return content

        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail="Content not allowed")

    def _internal_message_to_params(self, **kwargs):
        return {
            **kwargs,
            "model":self._model,
            "messages" : self._message_content,
        }

    def chat_completion_sync(self, **extra):
        params = self._internal_message_to_params(**extra)
        return self._llm.chat.completions.create(**params)

    async def chat_completion_async(self, **extra):
        params = self._internal_message_to_params(**extra)
        return await self._llm_async.chat.completions.create(**params)

    @abstractmethod
    def parameter_requirements(self):
        pass


    @abstractmethod
    async def run_async(self):
        pass

    @abstractmethod
    def run(self):
        pass


class DeepSeekLLM(LLMBase):
    _additional_params: dict = PrivateAttr(default=dict)

    def __init__(self, request: Request | None, content: str | list[dict]):
        super().__init__(request=request, content=content, model_type="LLM_TYPE_A")
        self._additional_params = {}


    def parameter_requirements(self, **kwargs):
        self._additional_params = kwargs.copy()
        return self


    def run(self):
        completion = self.chat_completion_sync(**self._additional_params)
        return completion.choices[0].message.content

    async def run_async(self):
        completion = await self.chat_completion_async(**self._additional_params)
        return completion.choices[0].message.content


class ReasoningLLM(LLMBase):
    _additional_params: dict = PrivateAttr(default=dict)
    def __init__(self, request: Request | None, content: str | list[dict]):
        super().__init__(request=request, content=content, model_type="LLM_TYPE_C")
        self._additional_params = {}

    def parameter_requirements(self, **kwargs):
        self._additional_params = kwargs.copy()
        return self


    def run(self):
        completion = self.chat_completion_sync(**self._additional_params)
        return completion.choices[0].message.content

    async def run_async(self):
        completion = await self.chat_completion_async(**self._additional_params)
        return completion.choices[0].message.content



class FastNonReasoningLLM(LLMBase):
    _additional_params: dict = PrivateAttr(default=dict)
    def __init__(self, request: Request | None, content: str | list[dict]):
        super().__init__(request=request, content=content, model_type="LLM_TYPE_D")
        self._additional_params = {}

    def parameter_requirements(self, **kwargs):
        self._additional_params = kwargs.copy()
        return self


    def run(self):
        completion = self.chat_completion_sync(**self._additional_params)
        return completion.choices[0].message.content

    async def run_async(self):
        completion = await self.chat_completion_async(**self._additional_params)
        return completion.choices[0].message.content