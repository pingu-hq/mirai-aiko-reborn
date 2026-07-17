from typing import Any
from crewai import Crew, Process, LLM
from functools import lru_cache
from app.core.agents.agent_loader import AgentLoader
from app.core.local_config import settings



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
    return LLM(model="groq/openai/gpt-oss-120b", **base_llm(), reasoning_effort="medium")




class CrewFactory:
    def __init__(self):
        self._agent_loader = None

    @property
    def agent_loader(self) -> AgentLoader:
        if self._agent_loader is None:
            self._agent_loader = AgentLoader()
        return self._agent_loader

    def build_crew(self, **kwargs):
        params = self.agent_loader.agents_and_tasks_as_params()
        return Crew(
            **params,
            process=Process.sequential,
            verbose=True,
            **kwargs
        )

    def run(self, inputs: dict[str, Any] | None = None,**kwargs) -> str:
        _crew_instance = self.build_crew(**kwargs)
        results = _crew_instance.kickoff(inputs=inputs) if inputs else _crew_instance.kickoff()
        return results.raw




def run_mirai_aiko():
    factory = CrewFactory()

    factory.agent_loader.create_agent("researcher", llm=small_llm())
    factory.agent_loader.create_agent("writer", llm=small_llm())
    factory.agent_loader.create_task("research_task", "researcher")
    factory.agent_loader.create_task("writing_task", "writer")
    result = factory.run()
    print(result)
    return result


# run_mirai_aiko()