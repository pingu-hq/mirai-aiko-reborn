from abc import ABC, abstractmethod
from typing import Optional
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.embeddings.cohere import CohereEmbedding
from app.core.local_config import settings
from app.core.logger import app_logger
from app.core.http_client import _httpx_sync_client, _httpx_async_client



_CHARACTER_INDEX: Optional[VectorStoreIndex] = None
_MESSAGE_INDEX: Optional[VectorStoreIndex] = None


_cohere_embedding_model: CohereEmbedding | None = None


def init_cohere_embedding_model():
    global _cohere_embedding_model
    if _cohere_embedding_model is None:
        app_logger.info("Starting cohere embed client!")
        cohere_params = {
            "model_name": "embed-multilingual-v3.0",
            "api_key": settings.cohere_api_key.get_secret_value(),
        }
        if _httpx_sync_client:
            cohere_params["httpx_client"] = _httpx_sync_client

        if _httpx_async_client:
            cohere_params["httpx_async_client"] = _httpx_async_client

        _cohere_embedding_model = CohereEmbedding(**cohere_params)



class MilvusVectorStoreBaseClass(ABC):

    @property
    @abstractmethod
    def milvus_vector_store(self) -> MilvusVectorStore:
        pass

    @property
    @abstractmethod
    def embed_model(self) -> CohereEmbedding:
        pass

    @staticmethod
    def create_index(vector_store, embed_model, use_async: bool = True):
        return VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=embed_model,
            use_async=use_async
        )





class CharacterKnowledgeRepository(MilvusVectorStoreBaseClass):

    @property
    def embed_model(self):
        return _cohere_embedding_model

    @property
    def milvus_vector_store(self) -> MilvusVectorStore:
        return app_state.milvus_character_vector

    @property
    def character_index(self):
        global _CHARACTER_INDEX
        if _CHARACTER_INDEX is None:

            _CHARACTER_INDEX = self.create_index(
                vector_store=self.milvus_vector_store,
                embed_model=self.embed_model,
            )
        return _CHARACTER_INDEX

class MessageStoreRepository(MilvusVectorStoreBaseClass):

    @property
    def embed_model(self):
        return _cohere_embedding_model

    @property
    def milvus_vector_store(self) -> MilvusVectorStore:
        return app_state.milvus_message_vector

    @property
    def message_index(self):
        global _MESSAGE_INDEX
        if _MESSAGE_INDEX is None:
            _MESSAGE_INDEX = self.create_index(
                vector_store=self.milvus_vector_store,
                embed_model=self.embed_model,
            )
        return _MESSAGE_INDEX

