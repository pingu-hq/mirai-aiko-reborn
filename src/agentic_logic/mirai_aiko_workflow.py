from src.agentic_workflows.azure_agents import MiraiAikoAgent
from src.data_storage.short_term_memory_store import MessageStore
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from cachetools import TTLCache
import asyncio



GRAPH_CACHE = TTLCache(maxsize=10, ttl=3600)



class StateChat(BaseModel):
    id: str = ""
    input_message: str = ""
    output_message: str = ""
    chat_history_holder: list[dict] = []



class GraphEngine:
    def __init__(self):
        self._workflow = StateGraph(StateChat)

    @staticmethod
    async def get_history(state: StateChat) -> dict:
        mem = MessageStore(user_id=state.id)
        history = await mem.add_user_message(input_message=state.input_message)
        return { 'chat_history_holder': history}

    @staticmethod
    async def mirai_aiko_agent(state: StateChat) -> dict:
        history = state.chat_history_holder
        agent = MiraiAikoAgent(input_message=history)
        output_message = await agent.aexecute()
        return {'output_message': output_message}

    @staticmethod
    async def update_memory(state: StateChat) -> dict:
        mem = MessageStore(user_id=state.id)
        final_chat_history = await mem.add_assistant_message(input_message=state.output_message)
        return {'chat_history_holder': final_chat_history}

    def workflow(self):
        w = self._workflow
        w.add_node("get_history", self.get_history)
        w.add_node("mirai_aiko_agent", self.mirai_aiko_agent)
        w.add_node("update_memory", self.update_memory)

        w.set_entry_point("get_history")
        w.add_edge("get_history", "mirai_aiko_agent")
        w.add_edge("mirai_aiko_agent", "update_memory")
        w.add_edge("update_memory", END)

        self._workflow = w
        return self._workflow



def get_compiled_workflow():
    loop = asyncio.get_running_loop()
    loop_id = id(loop)

    if loop_id not in GRAPH_CACHE:
        GRAPH_CACHE.expire()
        wf = GraphEngine()
        GRAPH_CACHE[loop_id] = wf.workflow().compile()

    return GRAPH_CACHE[loop_id]



class AgentWorkflow:
    def __init__(self, input_data: dict):
        self.data = input_data

    @property
    def workflow(self):
        return get_compiled_workflow()

    def execute(self):
        return self.workflow.invoke(self.data)

    async def aexecute(self):
        return await self.workflow.ainvoke(self.data)
