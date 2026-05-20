from src.agentic_workflows.azure_agents import MiraiAikoAgent
from src.data_storage.short_term_memory_store import MessageStore
from fastapi import APIRouter
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END


router = APIRouter(
    prefix="/api",
    tags=["api"]
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


class StateChat(BaseModel):
    id: str = ""
    input_message: str = ""
    output_message: str = ""
    chat_history_holder: list[dict] = []


async def get_history(state: StateChat):
    mem = MessageStore(user_id=state.id)
    state.chat_history_holder = await mem.add_user_message(input_message=state.input_message)
    return state

async def mirai_aiko_agent(state: StateChat):
    history = state.chat_history_holder
    agent = MiraiAikoAgent(input_message=history)
    state.output_message = await agent.aexecute()
    return state

async def update_memory(state: StateChat):
    mem = MessageStore(user_id=state.id)
    final_chat_history = await mem.add_assistant_message(input_message=state.output_message)
    state.chat_history_holder = final_chat_history
    return state


workflow = StateGraph(StateChat)
workflow.add_node("first_node", get_history)
workflow.add_node("second_node", mirai_aiko_agent)
workflow.add_node("third_node", update_memory)

workflow.set_entry_point("first_node")
workflow.add_edge("first_node", "second_node")
workflow.add_edge("second_node", "third_node")
workflow.add_edge("third_node", END)

app = workflow.compile()





