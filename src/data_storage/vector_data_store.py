from llama_index.core import VectorStoreIndex
from llama_index.core.schema import TextNode, BaseNode, MetadataMode, NodeWithScore
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
from llama_index.embeddings.cohere import CohereEmbedding
from src.core.local_config import settings
from datetime import timedelta, datetime, timezone
from functools import lru_cache



class ConfigLoader:
    def __init__(self):
        self.ttl = int(timedelta(days=7).total_seconds())
        self.coll_name = "temporary_message_collection"
        self.uri = settings.milvus_uri
        self.token = settings.milvus_token
        self.api_key = settings.cohere_api_key

    @property
    def load_vector_store(self):
        return MilvusVectorStore(
            uri=self.uri.get_secret_value(),
            token=self.token.get_secret_value(),
            collection_name=self.coll_name,
            overwrite=False,
            dim=1024,
            embedding_field="embeddings",
            search_config={"nprobe": 60},
            similarity_metric="COSINE",
            consistency_level="Session",
            collection_properties={"collection.ttl.seconds": self.ttl}
        )

    @property
    def load_embedding_model(self):
        return CohereEmbedding(
            model_name="embed-multilingual-v3.0",
            api_key=self.api_key.get_secret_value()
        )

    @property
    def load_index(self):
        return VectorStoreIndex.from_vector_store(
            use_async=True,
            vector_store=self.load_vector_store,
            embed_model=self.load_embedding_model
        )

@lru_cache()
def config_loader():
    return ConfigLoader()

class VectorDataStore:
    def __init__(self, user_id: str):
        self.config_loader = config_loader()
        self.index = self.config_loader.load_index
        self._id = user_id

    async def _ingest_text_to_index(self, text: str, metadata: dict | None):
        try:
            nodes: list[BaseNode] = [TextNode(
                text=text,
                metadata=metadata
            )]
            await self.index.ainsert_nodes(nodes=nodes)
        except Exception as ex:
            raise ex

    @property
    def filters(self):
        return MetadataFilters(
            filters=[
                ExactMatchFilter(key="name_of_user", value=self._id),
            ]
        )

    @staticmethod
    def node_cleansing(nodes: list[NodeWithScore]):
        cleansed_nodes = ""

        for i, n in enumerate(nodes):
            cleaned_meta = n.metadata.copy()
            cleaned_meta.pop("name_of_user", None)
            template = (
                f"<document_id='{i+1}>\n "
                f"<confidence_score>{n.score:.3f}</confidence_score>\n "
                f"<source_info>{cleaned_meta}</source_info>\n "
                f"<text_content>{n.get_content()}</text_content>\n "
                f"</document>\n "
            )
            cleansed_nodes += template
        return cleansed_nodes


    async def get_vector_by_query(self, query: str):
        try:
            as_retriever = self.index.as_retriever(similarity_top_k=3, filters=self.filters, )
            raw_node = await as_retriever.aretrieve(query)
            return self.node_cleansing(nodes=raw_node)
        except Exception as ex:
            raise ex


    async def ingest_text(self, content: str, metadata: dict | None = None):
        _date = datetime.now(timezone.utc)
        default_metadata = {
            "name_of_user" : self._id,
            "date_created": _date.date().isoformat(),
            "time_created": _date.time().isoformat(),
            "timezone":"utc"
        }
        if isinstance(metadata, dict):
            default_metadata.update(metadata)

        await self._ingest_text_to_index(text=content, metadata=default_metadata)