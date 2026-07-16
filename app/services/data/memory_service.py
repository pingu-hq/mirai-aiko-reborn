from mem0 import Memory
from app.core.local_config import settings
from langchain_cohere import CohereEmbeddings
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
            "reasoning_effort": "low",
        }
    },
    "embedder": {
        "provider": "langchain",
        "config": {
            "model": cohere_config
        }
    }

}

mem_zero = Memory.from_config(MEMO_CONFIG)



memory_client: Memory | None = None


def init_memory_client():
    global memory_client
    if memory_client is None:
        memory_client = Memory.from_config(MEMO_CONFIG)

class MemoryService:
    def __init__(self):
        self.mem_id = None

    @property
    def memory(self) -> Memory:
        return memory_client

    def add_memory(self, user_id: str, content: str):
        self.memory.add(user_id=user_id, messages=content)

    def search_memory(self, user_id: str, content: str):
        results = self.memory.search(query=content, filters={"user_id": user_id})
        self.mem_id = results["results"][0]["id"]
        return results

    def remove_memory(self, mem_id: str):
        try:
            self.memory.delete(memory_id=mem_id)
            return True
        except Exception as e:
            return False
