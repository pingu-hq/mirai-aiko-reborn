from src.core.local_config import settings
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.embeddings.cohere import CohereEmbedding
from datetime import timedelta



class MainMilvusClients:
    def __init__(self):
        self._embed_model = None
        self.api_key = settings.cohere_api_key
        self.uri = settings.milvus_uri
        self.token = settings.milvus_token
        self.ttl = int(timedelta(days=7).total_seconds())

    @property
    def embed_model(self):
        if self._embed_model is None:
            self._embed_model = CohereEmbedding(
                model_name="embed-multilingual-v3.0",
                api_key=self.api_key.get_secret_value()
            )
        return self._embed_model

    @property
    def character_knowledge_index(self):
        _vector_store = MilvusVectorStore(
            collection_name="character_knowledge_base",
            **self._vector_config_params()
        )
        return self._indexing(vector_store=_vector_store)

    @property
    def message_store_index(self):
        _vector_store = MilvusVectorStore(
            collection_name="temporary_message_collection",
            collection_properties={"collection.ttl.seconds": self.ttl},
            **self._vector_config_params()
        )
        return self._indexing(vector_store=_vector_store)

    def _indexing(self, vector_store: MilvusVectorStore):
        return VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=self.embed_model,
            use_async=True
        )

    def _vector_config_params(self):
        return {
            "uri" : self.uri.get_secret_value(),
            "token" : self.token.get_secret_value(),
            "overwrite" : False,
            "dim" : 1024,
            "embedding_field" : "embeddings",
            "search_config" : {"nprobe": 60},
            "similarity_metric" :  "COSINE",
            "consistency_level" : "Session",
        }


def lifespan_context_character_index():
    return MainMilvusClients().character_knowledge_index

def lifespan_context_message_index():
    return MainMilvusClients().message_store_index