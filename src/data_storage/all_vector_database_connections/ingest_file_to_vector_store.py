from src.core.local_config import settings
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import  Document
from llama_index.vector_stores.milvus import MilvusVectorStore
from llama_index.embeddings.cohere import CohereEmbedding
from pathlib import Path
import ulid
import yaml
import time



CREATE_NEW_FRESH_VECTOR = False
ALLOW_DATA_SOURCE_TO_BE_SAVED_IN_VECTOR = False



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
            overwrite=CREATE_NEW_FRESH_VECTOR,
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
    if not ALLOW_DATA_SOURCE_TO_BE_SAVED_IN_VECTOR:
        print("Please set the ALLOW_DATA_SOURCE_TO_BE_SAVED_IN_VECTOR to True if you want the file to go to vector database")
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


