from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.auth.opaque_auth_service import OpaqueAuthService
from app.services.agents.lotus_crew_service import LotusCrewService
from app.services.data.memory_service import AsyncMemZeroMemoryService
from app.dependencies.chat import get_async_mem_zero_service, get_lotus_crew_service
from app.dependencies.auth import get_opaque_auth_service



router = APIRouter(
    prefix="/api/chat", tags=["Send chat to Mirai Aiko Crew"]
)


class Chat(BaseModel):
    message: str

@router.post("/send", status_code=status.HTTP_200_OK)
async def send_messages(
        chat: Chat,
        opaque: OpaqueAuthService = Depends(get_opaque_auth_service),
        memory: AsyncMemZeroMemoryService = Depends(get_async_mem_zero_service),
        agent: LotusCrewService = Depends(get_lotus_crew_service)
):
    try:
        user_id = await opaque.get_user_id()
        current_memory = await memory.search_memory(user_id=user_id, content=chat.message)
        response = await agent.run_async(
            inputs={
                "user_id": user_id,
                "user_input": chat.message,
                "memory_context": current_memory
            }
        )
        return Chat(message=response)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error endpoint /send-message-to-mirai-aiko : {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request")