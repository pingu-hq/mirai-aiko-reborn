from src.agentic_workflows.azure_agents import MiraiAikoAgent
from src.data_storage.short_term_memory_store import MessageStore
from fastapi import APIRouter
from pydantic import BaseModel, Field


router = APIRouter(
    prefix="/chatbot",
    tags=["chatbot"]
)

class SendMessage(BaseModel):
    text: str = Field(default="", description="Text to send")
    id: str


@router.post("/send-message")
async def api_send_message(message: SendMessage):
    mem = MessageStore(user_id=message.id)
    history = await mem.add_user_message(message.text)
    agent = MiraiAikoAgent(input_message=history)
    response = await agent.aexecute()
    await mem.add_assistant_message(response)
    return SendMessage(text=response, id=message.id)
