from typing import Any
from app.core.agents.crew_factory import CrewFactory, small_llm, large_llm






class LotusCrewService:
    def __init__(self):
        self.factory = CrewFactory()
        self.gpt_oss_20 = small_llm()
        self.gpt_oss_120 = large_llm()

    def initialize_agents(self):
        try:
            self.factory.agent_loader.create_agent(agent_name="researcher", llm=self.gpt_oss_20)
            self.factory.agent_loader.create_agent(agent_name="writer", llm=self.gpt_oss_120)
            return self
        except Exception as e:
            raise e

    def initialize_tasks(self):
        try:
            self.factory.agent_loader.create_task(task_name="research_task", agent_assigned="researcher")
            self.factory.agent_loader.create_task(task_name="writing_task", agent_assigned="writer")
            return self
        except Exception as e:
            raise e

    def run(self, inputs: dict[str, Any], **kwargs):
        try:
            self.initialize_agents()
            self.initialize_tasks()
            return self.factory.run(inputs=inputs, **kwargs)
        except Exception as e:
            raise e

    async def run_async(self, inputs: dict[str, Any], **kwargs):
        try:
            self.initialize_agents()
            self.initialize_tasks()
            return await self.factory.run_async(inputs=inputs, **kwargs)
        except Exception as e:
            raise e