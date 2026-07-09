from abc import ABC, abstractmethod
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.embeddings.cohere import CohereEmbedding
from datetime import timedelta
from app.core.local_config import settings
from app.core.logger import app_logger
from app.core.http_client import _httpx_sync_client, _httpx_async_client



_cohere_embedding_model: CohereEmbedding | None = None

_character_vector_store: MilvusVectorStore | None = None
_message_vector_store: MilvusVectorStore | None = None

_character_index: VectorStoreIndex | None = None
_message_index: VectorStoreIndex | None = None


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

def _vector_config_params():
    return {
        "uri" : settings.milvus_uri.get_secret_value(),
        "token" : settings.milvus_token.get_secret_value(),
        "overwrite" : False,
        "dim" : 1024,
        "embedding_field" : "embeddings",
        "search_config" : {"nprobe": 60},
        "similarity_metric" :  "COSINE",
        "consistency_level" : "Session",
    }

def init_milvus_character_knowledge():
    global _character_vector_store
    if _character_vector_store is None:
        app_logger.info("Starting milvus character knowledge!")
        other_params = _vector_config_params()
        _character_vector_store = MilvusVectorStore(
            collection_name="character_knowledge_base",
            **other_params
        )

def init_milvus_message_store():
    global _message_vector_store
    if _message_vector_store is None:
        app_logger.info("Starting milvus message store!")
        _ttl = int(timedelta(days=7).total_seconds())
        other_params = _vector_config_params()
        _message_vector_store = MilvusVectorStore(
            collection_name="temporary_message_collection",
            collection_properties={"collection.ttl.seconds": _ttl},
            **other_params
        )

def close_milvus_character_knowledge():
    global _character_vector_store
    if _character_vector_store:
        _character_vector_store.client.close()


def close_milvus_message_store():
    global _message_vector_store
    if _message_vector_store:
        _message_vector_store.client.close()



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
        if _character_vector_store is None:
            raise RuntimeError("Milvus vector store for character knowledge not initialized.")
        return _character_vector_store


    @property
    def character_index(self):
        global _character_index
        if _character_index is None:
            _character_index = self.create_index(
                vector_store=self.milvus_vector_store,
                embed_model=self.embed_model,
            )
        return _character_index

class MessageStoreRepository(MilvusVectorStoreBaseClass):

    @property
    def embed_model(self):
        return _cohere_embedding_model

    @property
    def milvus_vector_store(self) -> MilvusVectorStore:
        if _message_vector_store is None:
            raise RuntimeError("Milvus vector store for message store not initialized.")
        return _message_vector_store

    @property
    def message_index(self):
        global _message_index
        if _message_index is None:
            _message_index = self.create_index(
                vector_store=self.milvus_vector_store,
                embed_model=self.embed_model,
            )
        return _message_index

