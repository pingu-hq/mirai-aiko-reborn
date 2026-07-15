from crewai import Crew, Process
from app.core.agents.agent_loader import AgentLoader
from app.core.local_config import settings
import os


os.environ["GROQ_API_KEY"] = settings.groq_api_key.get_secret_value()




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
    _researcher = agent_loader.create_agent("researcher", llm="groq/openai/gpt-oss-20b")
    _writer = agent_loader.create_agent("writer", llm="groq/openai/gpt-oss-20b")
    agent_loader.create_task("research_task", _researcher)
    agent_loader.create_task("writing_task", _writer)
    crew_instance = CrewFactory(agent_loader)
    the_crew = crew_instance.create_crew()
    result = the_crew.kickoff()
    print(result.raw)


run_mirai_aiko()