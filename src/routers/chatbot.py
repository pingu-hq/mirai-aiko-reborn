from src.agentic_workflows.azure_agents import MiraiAikoAgent
from src.data_storage.short_term_memory_store import MessageStore
from src.agentic_workflows.mirai_aiko_workflow import app as ai_agent, StateChat
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



@router.post("/send-message-v1")
async def api_send_message_v1(message: SendMessage):
    state = StateChat(
        id=message.id,
        input_message=message.text
    )
    response = await ai_agent.ainvoke(state)
    return response