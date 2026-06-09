from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from app.repositories.no_sql_database.milvus_vector_repository import MessageStoreRepository
from app.services.data.message_vector_services import MessageVectorService
from app.services.agents.sample_agent_service import AgentService

from app.repositories.in_memory_database.redis_repository import JtiCacheRepository
from app.services.auth.web_auth_service import (
    JwtTokenService,
    HttpCookieManagerService,
    JwtAndCookieHandlerService
)


def get_message_store_repository() -> MessageStoreRepository:
    return MessageStoreRepository()

def get_message_vector_service(
        message_repository: MessageStoreRepository = Depends(get_message_store_repository)
) -> MessageVectorService:

    return MessageVectorService(message_repository=message_repository)

def agent_service(
        message_vector_service: MessageVectorService = Depends(get_message_vector_service)
) -> AgentService:

    return AgentService(message_vector_service=message_vector_service)

def get_jti_repo() -> JtiCacheRepository:
    return JtiCacheRepository()

def get_jwt_service(jti_repo: JtiCacheRepository = Depends(get_jti_repo)) -> JwtTokenService:
    return JwtTokenService(jti_repo)

def get_jwt_cookie_handler(request: Request, response: Response) -> JwtAndCookieHandlerService:
    return JwtAndCookieHandlerService(request=request, response=response)

def http_cookie_service(
        jwt_service: JwtTokenService = Depends(get_jwt_service),
        auth_handler_service: JwtAndCookieHandlerService = Depends(get_jwt_cookie_handler)
) -> HttpCookieManagerService:
    return HttpCookieManagerService(
        jwt_service=jwt_service,
        auth_handler_service=auth_handler_service
    )

router = APIRouter(
    prefix="/api/chat", tags=["chat"]
)


class Chat(BaseModel):
    message: str

@router.post("/send", status_code=status.HTTP_200_OK)
async def send_messages(
        chat: Chat,
        http_cookie: HttpCookieManagerService = Depends(http_cookie_service),
        agent: AgentService = Depends(agent_service)
):
    try:
        user_id = http_cookie.getting_id_from_http_cookie()
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not found")

        assistant_response = await agent.full_message_completion(
            user_id=user_id,
            content=chat.message
        )
        return Chat(message=assistant_response)
    except Exception as e:
        print(f"Error endpoint /send : {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))