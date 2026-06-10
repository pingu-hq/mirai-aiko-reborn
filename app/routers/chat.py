from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.agents.sample_agent_service import AgentService
from app.services.auth.web_auth_service import  HttpCookieManagerService
from app.dependencies.auth import get_http_cookie_manager_service
from app.dependencies.chat import get_agent_service



router = APIRouter(
    prefix="/api/chat", tags=["chat"]
)


class Chat(BaseModel):
    message: str

@router.post("/send", status_code=status.HTTP_200_OK)
async def send_messages(
        chat: Chat,
        http_cookie: HttpCookieManagerService = Depends(get_http_cookie_manager_service),
        agent: AgentService = Depends(get_agent_service)
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