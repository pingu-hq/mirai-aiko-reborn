from fastapi import HTTPException, Request
from src.core.local_config import settings
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore, Document
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.embeddings.cohere import CohereEmbedding
from pathlib import Path
import ulid
import yaml
import time




IS_DEVELOPMENT = False

class VectorClientLoader:
    def __init__(self):
        self.coll_name = "character_knowledge_base"
        self.uri = settings.milvus_uri
        self.token = settings.milvus_token
        self.api_key = settings.cohere_api_key

    @property
    def load_vector_store(self):
        return MilvusVectorStore(
            uri=self.uri.get_secret_value(),
            token=self.token.get_secret_value(),
            collection_name=self.coll_name,
            overwrite=IS_DEVELOPMENT,
            dim=1024,
            embedding_field="embeddings",
            search_config={"nprobe": 60},
            similarity_metric="COSINE",
            consistency_level="Session",
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

DATA_SOURCE_PATH = None

def ingest_pipeline(name_of_file: str | None = None):
    if not IS_DEVELOPMENT:
        return None
    if name_of_file is None:
        return None

    start_time_of_path = time.monotonic()

    global DATA_SOURCE_PATH
    if DATA_SOURCE_PATH is None:
        DATA_SOURCE_PATH = Path(__file__).resolve().parent / "data_sources"

    time_of_path_creation = time.monotonic()
    print("Time of creating and finding path is: ", (time_of_path_creation - start_time_of_path))

    with open(DATA_SOURCE_PATH / name_of_file, 'r') as f:
        yaml_data = yaml.safe_load(f)

    time_of_yaml_loading = time.monotonic()
    print("Time yaml file to safely load to python is : ", (time_of_yaml_loading - time_of_path_creation))

    raw_text_nodes = []
    for content in yaml_data:
        raw_text_nodes.append(Document(**content, id_=ulid.new().str))

    time_of_sending_yaml_to_nodes = time.monotonic()
    print("Time of yaml file to nodes is : ", (time_of_sending_yaml_to_nodes - time_of_yaml_loading))

    vector_engine = VectorClientLoader()
    index = vector_engine.load_index

    time_of_index_creation_or_connection = time.monotonic()
    print("Time of index creation and connection to client is : ", (time_of_index_creation_or_connection - time_of_sending_yaml_to_nodes))

    index.insert_nodes(raw_text_nodes)

    time_of_insert_nodes_to_vector = time.monotonic()
    print("Time of insert nodes to vector is : ", (time_of_insert_nodes_to_vector - time_of_index_creation_or_connection))

    return True

ingest_pipeline("character_knowledge_base.yaml")




def lifespan_context_vector_store_index():
    return VectorClientLoader().load_index


class CharacterKnowledgeBase:
    def __init__(self, request: Request):
        self.request = request

    @property
    def index(self) -> VectorStoreIndex:
        return self.request.app.state.vector_store_index

    @staticmethod
    def _memory_organizer(raw_memories: list[NodeWithScore]):
        cleansed_parts = []

        for i, mem in enumerate(raw_memories):
            score = f"{mem.score:.3f}"
            description = mem.metadata.get("description", "No description available.")
            dialogue = mem.metadata.get("dialogue", "")

            template = (
                f"<memory_node index='{i + 1}'>\n"
                f"  <confidence>{score}</confidence>\n"
                f"  <trait>{description}</trait>\n"
                f"  <behavioral_sample>{dialogue}</behavioral_sample>\n"
                f"</memory_node>"
            )
            cleansed_parts.append(template)

        final_context = "<retrieved_memories>\n" + "\n".join(cleansed_parts) + "\n</retrieved_memories>"
        return final_context

    async def search_memories_by_query(self, query: str):
        memories = self.index.as_retriever(similarity_top_k=5)
        raw_memories = await memories.aretrieve(query)
        cleaned_memories = self._memory_organizer(raw_memories=raw_memories)
        return cleaned_memories