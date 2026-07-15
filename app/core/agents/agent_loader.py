from pathlib import Path
from functools import lru_cache
from crewai import Agent, Task
from yaml import safe_load as yaml_load



FILES_AVAIL = (
    "agents.yaml",
    "tasks.yaml",
)

@lru_cache(maxsize=len(FILES_AVAIL))
def load_yaml(filename: str) -> dict:
    if filename not in FILES_AVAIL:
        raise ValueError(f"Config file '{filename}' not in allowed list: {FILES_AVAIL}")
    config_path = Path(__file__).parent / "config" / filename
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml_load(f)

def init_yaml_loader():
    for file in FILES_AVAIL:
        load_yaml(filename=file)



class AgentLoader:
    def __init__(self):
        self._agents: list[Agent] = []
        self._tasks: list[Task] = []

    @property
    def agents_yaml(self):
        return load_yaml(filename="agents.yaml")

    @property
    def tasks_yaml(self):
        return load_yaml(filename="tasks.yaml")


    def create_agent(self, agent_name: str, **overrides) -> Agent:
        config_file = self.agents_yaml[agent_name]
        new_agent = Agent(**config_file, **overrides)
        self._agents.append(new_agent)
        return new_agent

    def create_task(self, task_name: str, agent_assigned: Agent, **overrides) -> Task:
        config_file = self.tasks_yaml[task_name]
        new_task = Task(**config_file, agent=agent_assigned, **overrides)
        self._tasks.append(new_task)
        return new_task

    def agents_and_tasks_as_params(self) -> dict[str, list[Agent] | list[Task]]:
        return {"agents": self._agents, "tasks": self._tasks}

