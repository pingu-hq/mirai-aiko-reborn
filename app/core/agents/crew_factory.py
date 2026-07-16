from crewai import Crew, Process, LLM
from functools import lru_cache
from app.core.agents.agent_loader import AgentLoader
from app.core.local_config import settings
import os



def base_llm():
    return {
        "base_url":"https://api.groq.com/openai/v1",
        "max_completion_tokens":10_000, "temperature":.5,
        "api_key":settings.groq_api_key.get_secret_value(),    "top_p":1,
    }

@lru_cache()
def small_llm():
    return LLM(model="groq/openai/gpt-oss-20b", **base_llm(), reasoning_effort="medium")

@lru_cache()
def large_llm():
    return LLM(model="groq/openai/gpt-oss-120b", **base_llm(), reasoning_effort="low",    tools=[{"type":"browser_search"}])




class CrewFactory:
    def __init__(self, agent_loader: AgentLoader):
        self._agent_loader = agent_loader

    def create_crew(self) -> Crew:
        params = self._agent_loader.agents_and_tasks_as_params()
        return Crew(
            **params,
            process=Process.sequential,
            verbose=True
        )


def run_mirai_aiko():
    agent_loader = AgentLoader()
    agent_loader.create_agent("researcher", llm=small_llm())
    agent_loader.create_agent("writer", llm=small_llm())
    agent_loader.create_task("research_task", "researcher")
    agent_loader.create_task("writing_task", "writer")
    crew_instance = CrewFactory(agent_loader)
    the_crew = crew_instance.create_crew()
    result = the_crew.kickoff()
    print(result.raw)


run_mirai_aiko()