from typing import Literal
from mem0 import Memory, AsyncMemory
from app.core.local_config import settings
from langchain_cohere import CohereEmbeddings
from json import dumps
import os


os.environ["COHERE_API_KEY"] = settings.cohere_api_key.get_secret_value()
os.environ["GROQ_API_KEY"] = settings.groq_api_key.get_secret_value()



cohere_config = CohereEmbeddings(model="embed-v4.0")




MEMO_CONFIG = {
    "vector_store": {
        "provider": "milvus",
        "config": {
            "url": settings.milvus_uri.get_secret_value(),
            "token": settings.milvus_token.get_secret_value(),
            "collection_name": "mirai_aiko_memories",
            "embedding_model_dims": 1536,
        }
    },
    "llm": {
        "provider":"groq",
        "config": {
            "model":"openai/gpt-oss-20b",
            "temperature": 0.3,
            "max_tokens": 10_000,
            "reasoning_effort": "medium",
        }
    },
    "embedder": {
        "provider": "langchain",
        "config": {
            "model": cohere_config
        }
    }

}


memory_client: Memory | None = None
async_memory_client: AsyncMemory | None = None


def init_memory_client():
    global memory_client
    if memory_client is None:
        memory_client = Memory.from_config(MEMO_CONFIG)

def close_memory_client():
    global memory_client
    if memory_client:
        memory_client.close()

class MemZeroMemoryService:
    def __init__(self):
        self.mem_id: list[str] = []

    @property
    def memory(self) -> Memory:
        return memory_client

    def add_memory(self, user_id: str, content: str):
        self.memory.add(user_id=user_id, messages=content)

    def search_memory(self, user_id: str, content: str, output: Literal["str", "raw"] = "str") -> str | list[dict]:
        results = self.memory.search(query=content, filters={"user_id": user_id})
        self._id_extractor(search_results=results)
        cleaned_data = self.cleaned_searched_result(search_results=results)
        if output == "str":
            return dumps(cleaned_data)
        return cleaned_data

    def remove_memory(self, mem_id: str | None = None):
        try:
            if mem_id:
                self.memory.delete(memory_id=mem_id)
                return True

            for mem in self.mem_id:
                self.memory.delete(memory_id=mem)

            self.mem_id = []
            return True
        except Exception as e:
            return False

    def _id_extractor(self, search_results: dict[str, list[dict]]):
        for sr in search_results["results"]:
            memory_id = sr["id"]
            self.mem_id.append(memory_id)

    @staticmethod
    def cleaned_searched_result(search_results: dict[str, list[dict]]) -> list[dict]:
        cleaned_data = []
        for sr in search_results["results"]:

            timestamps = {"created_at": sr["created_at"]}

            if sr["created_at"] != sr["updated_at"]:
                timestamps["updated_at"] = sr["updated_at"]

            result_data = {
                "memory": sr['memory'],
                "metadata": sr['metadata'],
                "score": sr['score'],
                **timestamps
            }
            cleaned_data.append(result_data)
        return cleaned_data


class AsyncMemZeroMemoryService:

    @property
    def memory_client(self) -> AsyncMemory:
        global async_memory_client
        if async_memory_client is None:
            async_memory_client = AsyncMemory.from_config(MEMO_CONFIG)
        return async_memory_client

    async def add_memory(self, user_id: str, content: str):
        await self.memory_client.add(user_id=user_id, messages=content)

    async def search_memory(self, user_id: str, content: str, output: Literal["str", "raw"] = "str"):
        results = await self.memory_client.search(query=content, filters={"user_id": user_id})
        cleaned_data = self.cleaned_searched_result(search_results=results)
        if output == "str":
            return dumps(cleaned_data)
        return cleaned_data

    @staticmethod
    def cleaned_searched_result(search_results: dict[str, list[dict]]) -> list[dict]:
        cleaned_data = []
        for sr in search_results["results"]:

            timestamps = {"created_at": sr["created_at"]}

            if sr["created_at"] != sr["updated_at"]:
                timestamps["updated_at"] = sr["updated_at"]

            result_data = {
                "memory": sr['memory'],
                "metadata": sr['metadata'],
                "score": sr['score'],
                **timestamps
            }
            cleaned_data.append(result_data)
        return cleaned_data