from src.agentic_workflows.mirai_aiko_workflow import AgentWorkflow
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(
    prefix="/chatbot",
    tags=["chatbot"]
)

class SendMessage(BaseModel):
    input_message: str = Field(default="", description="Text to send")
    id: str


@router.post("/send-message")
async def api_send_message(message: SendMessage):
    try:
        agent = AgentWorkflow(message.model_dump())
        response = await agent.aexecute()
        return response
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=400, detail="Bad Request")