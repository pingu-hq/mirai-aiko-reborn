from app.services.agents.sample_agent_service import AgentService
from app.services.data.message_vector_services import MessageVectorService
from app.repositories.no_sql_database.milvus_vector_repository import MessageStoreRepository
from fastapi import Depends



def get_message_store_repository() -> MessageStoreRepository:
    return MessageStoreRepository()


def get_message_vector_service(
        message_repository: MessageStoreRepository = Depends(get_message_store_repository)
):
    return MessageVectorService(
        message_repository=message_repository
    )


def get_agent_service(
    message_vector_service: MessageVectorService = Depends(get_message_vector_service)
) -> AgentService:
    return AgentService(message_vector_service=message_vector_service)