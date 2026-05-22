from llama_index.core import VectorStoreIndex
from llama_index.core.schema import TextNode, BaseNode, NodeWithScore
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
from fastapi import Request
from datetime import datetime, timezone



class MessageVectorStore:
    def __init__(self, user_id: str, request: Request):
        self.request = request
        self._id = user_id

    @property
    def index(self) -> VectorStoreIndex:
        return self.request.app.state.message_index

    @property
    def id(self):
        return self._id

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
                ExactMatchFilter(key="name_of_user", value=self.id),
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
            "name_of_user" : self.id,
            "date_created": _date.date().isoformat(),
            "time_created": _date.time().isoformat(),
            "timezone":"utc"
        }
        if isinstance(metadata, dict):
            default_metadata.update(metadata)

        await self._ingest_text_to_index(text=content, metadata=default_metadata)