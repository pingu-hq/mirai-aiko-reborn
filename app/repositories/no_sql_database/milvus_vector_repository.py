from abc import ABC, abstractmethod
from typing import Optional
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.embeddings.cohere import CohereEmbedding
from app.core.state import app_state



_CHARACTER_INDEX: Optional[VectorStoreIndex] = None
_MESSAGE_INDEX: Optional[VectorStoreIndex] = None



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
        return app_state.cohere_embed_model

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
        return app_state.cohere_embed_model

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

