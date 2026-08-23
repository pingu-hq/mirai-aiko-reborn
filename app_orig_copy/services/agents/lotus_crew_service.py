from typing import Any
from crewai import Crew, Process, Agent
from crewai.crews.crew_output import CrewOutput
from app.core.agents.agent_loader import SampleAgentLoader
from app.core.agents.llm_loader import LLMLoader
from pydantic import BaseModel, Field
from app.core.logger import app_logger




class LotusRoutingResult(BaseModel):
    assumptions: str = Field(description="The core intent and context assumptions")
    detected_language: str = Field(description="The language and any slang detected")
    needs_translation: bool = Field(description="True if translation is needed")
    needs_web_search: bool = Field(description="True if real-time web search is required")
    needs_internal_knowledge: bool = Field(description="True if internal lookup is needed")
    needs_memory_update: bool = Field(description="True if mem0 needs updating")



class LotusCrewService:
    def __init__(self):
        self.al = SampleAgentLoader()
        self.llm_loader = LLMLoader()
        # self.groq_llm = self.llm_loader.get_groq_llm("big", "low")
        # self.al.create_agent(
        #     agent_name="lotus_analyzer",
        #     llm=self.groq_llm)
        # self.al.create_task(
        #     task_name="filter_and_clean_task",
        #     agent_assigned="lotus_analyzer")
        # self.al.create_task(
        #     task_name="assumption_and_routing_task",
        #     agent_assigned="lotus_analyzer",
        #     output_pydantic=LotusRoutingResult)



    def analyzer_agent(self):
        self.al.agents_yaml[""]
        return Agent(

        )

    def get_crew(self, **kwargs) -> Crew:
        kwargs.setdefault("verbose", True)
        kwargs.setdefault("process", Process.sequential)
        kwargs.setdefault("agents", self.al.all_agents)
        kwargs.setdefault("tasks", self.al.all_tasks)
        return Crew(**kwargs)

    async def run(self, user_input: str, memory_context: Any, **kwargs):
        crew = self.get_crew(**kwargs)
        inputs = {"user_input": user_input, "memory_context": memory_context}
        result: CrewOutput = await crew.kickoff_async(inputs=inputs)
        return result.pydantic



async def lotus_async_execution(user_input: str, memory_context: Any):
    if memory_context is None:
        memory_context = "No previous memory context available."
    app_logger.debug(f"Starting Lotus Crew with Input: {user_input} | Context: {memory_context}")
    lcs = LotusCrewService()
    crew_created = lcs.get_crew()
    result = await crew_created.kickoff_async({"user_input": user_input, "memory_context": memory_context})
    app_logger.debug(f"Type{type(result)} // Results content: {result.raw}")
    return result
