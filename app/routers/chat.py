from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.agents.sample_agent_service import AgentService
from app.dependencies.auth import get_user_id_from_cookie
from app.dependencies.chat import get_agent_service



router = APIRouter(
    prefix="/api/chat", tags=["chat"]
)


class Chat(BaseModel):
    message: str

@router.post("/send", status_code=status.HTTP_200_OK)
async def send_messages(
        chat: Chat,
        user_id: str = Depends(get_user_id_from_cookie),
        agent: AgentService = Depends(get_agent_service)
):
    try:
        assistant_response = await agent.full_message_completion(
            user_id=user_id,
            content=chat.message
        )
        return Chat(message=assistant_response)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error endpoint /send : {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))