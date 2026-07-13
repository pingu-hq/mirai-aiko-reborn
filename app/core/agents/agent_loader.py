from pathlib import Path
from typing import Literal

from crewai import Agent, Task
from app.core.exceptions import custom_check_runtime
import yaml

agent_config_yaml: dict | None = None
task_config_yaml: dict | None = None


files_available = Literal[
    "agents.yaml",
    "tasks.yaml"
]


class AgentLoader:
    def __init__(self):
        self._agents = []
        self._tasks = []

    def init_config(self):
        global agent_config_yaml, task_config_yaml
        if agent_config_yaml is None:
            agent_config_yaml = self.load_yaml("agents.yaml")
        if task_config_yaml is None:
            task_config_yaml = self.load_yaml("tasks.yaml")

    @staticmethod
    def runtime_checker(variable_to_check):
        return custom_check_runtime(variable_to_check, "Yaml config file not initialized")

    @staticmethod
    def load_yaml(filename: files_available) -> dict:
        config_path = Path(__file__).parent / 'config' / filename
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def load_agent_config(self, agent_name: str) -> dict:
        checked_config = self.runtime_checker(variable_to_check=agent_config_yaml)
        return checked_config[agent_name]

    def load_task_config(self, task_name: str) -> dict:
        checked_config = self.runtime_checker(variable_to_check=task_config_yaml)
        return checked_config[task_name]

    def create_agent(self, agent_name: str, **overrides) -> Agent:
        config_file = self.load_agent_config(agent_name=agent_name)
        new_agent = Agent(**config_file, **overrides)
        self._agents.append(new_agent)
        return new_agent

    def create_task(self, task_name: str, agent_assigned: Agent, **overrides) -> Task:
        config_file = self.load_task_config(task_name=task_name)
        new_task = Task(**config_file, agent=agent_assigned, **overrides)
        self._tasks.append(new_task)
        return new_task

    def load_agents_and_tasks(self) -> tuple[list[Agent], list[Task]]:
        for agent in self._agents:
            if not isinstance(agent, Agent) or self._agents is []:
                raise RuntimeError("Agent is not an Agent")
        for task in self._tasks:
            if not isinstance(task, Task) or self._tasks is []:
                raise RuntimeError("Task is not a Task")

        return self._agents, self._tasks

def init_yaml_loader():
    AgentLoader().init_config()
