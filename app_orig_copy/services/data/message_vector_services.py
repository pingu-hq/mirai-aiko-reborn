from app.repositories.no_sql_database.milvus_vector_repository import MessageStoreRepository
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import TextNode, BaseNode, NodeWithScore
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
from datetime import datetime
from zoneinfo import ZoneInfo


class RawMessageDataHandler:

    @staticmethod
    def node_cleansing(input_message_key: str, nodes: list[NodeWithScore]):
        cleansed_nodes = ""

        for i, n in enumerate(nodes):
            cleaned_meta = n.metadata.copy()
            cleaned_meta.pop(input_message_key, None)
            template = (
                f"<document_id='{i + 1}>\n "
                f"<confidence_score>{n.score:.3f}</confidence_score>\n "
                f"<source_info>{cleaned_meta}</source_info>\n "
                f"<text_content>{n.get_content()}</text_content>\n "
                f"</document>\n "
            )
            cleansed_nodes += template
        return cleansed_nodes

    @staticmethod
    def pre_processing_node(input_user_key: str, content: str, metadata: dict | None = None) -> list[BaseNode]:
        ph_tz = ZoneInfo("Asia/Manila")
        current_datetime = datetime.now(ph_tz)
        default_metadata = {
            "message_vector_user_id": input_user_key,
            "date_created": current_datetime.date().isoformat(),
            "time_created": current_datetime.time().isoformat(),
            "timezone": "ph"
        }
        if metadata:
            default_metadata.update(metadata)

        return [TextNode(text=content, metadata=default_metadata)]




class MessageVectorService:
    def __init__(self, message_repository: MessageStoreRepository):
        self._message_repository = message_repository
        self.message_key = "message_vector_user_id"

    @property
    def index(self) -> VectorStoreIndex:
        if not self._message_repository:
            raise RuntimeError("Message Store Repository is not injected")
        return self._message_repository.message_index


    def filters(self, input_user_id) -> MetadataFilters:
        return MetadataFilters(
            filters=[
                ExactMatchFilter(
                    key=self.message_key,
                    value=input_user_id)
            ]
        )

    def retriever_engine(self, input_user_id):
        return self.index.as_retriever(
            similarity_top_k=5,
            filters=self.filters(input_user_id)
        )


    async def retrieve_data_async(self, user_id: str, content: str) -> str:
        retriever_engine = self.retriever_engine(user_id)
        raw_nodes =  await retriever_engine.aretrieve(content)
        return RawMessageDataHandler.node_cleansing(
            input_message_key=user_id,
            nodes=raw_nodes
        )

    async def insert_data_async(self, user_id: str, content: str, metadata: dict | None = None):
        pre_processed_nodes = RawMessageDataHandler.pre_processing_node(
            input_user_key=user_id,
            content=content,
            metadata=metadata
        )
        await self.index.ainsert_nodes(nodes=pre_processed_nodes)