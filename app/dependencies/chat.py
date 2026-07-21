from app.services.data.message_vector_services import MessageVectorService
from app.repositories.no_sql_database.milvus_vector_repository import MessageStoreRepository
from app.services.agents.lotus_crew_service import LotusCrewService
from app.services.data.memory_service import MemZeroMemoryService, AsyncMemZeroMemoryService
from fastapi import Depends



def get_message_store_repository() -> MessageStoreRepository:
    return MessageStoreRepository()


def get_message_vector_service(
        message_repository: MessageStoreRepository = Depends(get_message_store_repository)
):
    return MessageVectorService(
        message_repository=message_repository
    )

def get_lotus_crew_service():
    return LotusCrewService()

def get_mem_zero_service():
    return MemZeroMemoryService()

def get_async_mem_zero_service():
    return AsyncMemZeroMemoryService()