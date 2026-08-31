import os
from json import dumps
from typing import Literal

from langchain_cohere import CohereEmbeddings
from mem0 import AsyncMemory

from app.core.config import settings

os.environ["COHERE_API_KEY"] = settings.cohere_api_key
os.environ["GROQ_API_KEY"] = settings.groq_api_key



MEMO_CONFIG = {
    "vector_store": {
        "provider": "milvus",
        "config": {
            "url": settings.milvus_config["uri"],
            "token": settings.milvus_config["token"],
            "collection_name": settings.milvus_config["collection_name"],
            "embedding_model_dims": 1536,
        }
    },
    "llm": {
        "provider":"groq",
        "config": {
            "model":"openai/gpt-oss-120b",
            "temperature": 0.3,
            "max_tokens": 10_000,
            "reasoning_effort": "medium",
        }
    },
    "embedder": {
        "provider": "langchain",
        "config": {
            "model": CohereEmbeddings(
                model="embed-v4.0",
                client=None,
                async_client=None
            )  
        }
    }

}




class AgentMemoryRepository:
    _async_memory_client: AsyncMemory | None = None

    @classmethod
    def init_memory_client(cls):
        if cls._async_memory_client is None:
            cls._async_memory_client = AsyncMemory.from_config(MEMO_CONFIG)

    @classmethod
    def close_memory_client(cls):
        if cls._async_memory_client:
            cls._async_memory_client.close()
            cls._async_memory_client = None

    @property
    def memory_client(self) -> AsyncMemory:
        if self._async_memory_client is None:
            raise RuntimeError("Memory client not initialized")
        return self._async_memory_client

    async def add_memory(self, user_id: str, content: str):
        await self.memory_client.add(user_id=user_id, messages=content)

    async def search_memory(self, user_id: str, content: str, output: Literal["str", "raw"] = "str", **kwargs):
        results = await self.memory_client.search(query=content, filters={"user_id": user_id}, **kwargs)
        cleaned_data = self.cleaned_searched_result(search_results=results)
        if output == "str":
            return dumps(cleaned_data)
        return cleaned_data

    async def raw_search_memory(
            self, user_id: str,
            query: str,
            output: Literal["str", "raw"] = "str",
            explain: bool = False
    ) -> str | dict:

        results = await self.memory_client.search(
            query=query,
            filters={"user_id": user_id},
            explain=explain
        )
        if output == "str":
            return dumps(results)
        return results

    @staticmethod
    def cleaned_searched_result(search_results: dict[str, list[dict]]) -> list[dict]:
        allowed_fields = {
            "memory",
            "metadata",
            "score",
            "score_details",
            "created_at",
            "updated_at",
        }

        return [
            {key: value for key, value in sr.items() if key in allowed_fields}
            for sr in search_results.get("results", [])
        ]
