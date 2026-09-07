from crewai import Agent, Task, Process, Crew
from yaml import safe_load
from pathlib import Path
from enum import StrEnum


class AgentName(StrEnum):
    AGENT_1 = 'context_dialogue_synthesizer'

class TaskName(StrEnum):
    TASK_1 = 'context_intent_analysis'
    TASK_2 = 'final_response_generation'


class YamlLoader:
    _base_path = Path(__file__).resolve().parent
    agent_yaml_path: Path = _base_path / 'agents_list.yaml'
    tasks_yaml_path: Path = _base_path / 'tasks_list.yaml'

    def __init__(self):
        self.agents_list = self.load_yaml_files(self.agent_yaml_path)
        self.tasks_list = self.load_yaml_files(self.tasks_yaml_path)


    def load_yaml_files(self, file_path: Path) -> dict[str, str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")

class AgentCreation:
    _agent_list: dict[str, str] | None = None

    @classmethod
    def get_agent_list(cls):
        if not cls._agent_list:
            cls._agent_list = YamlLoader().agents_list
        return cls._agent_list

    def get_agent_config(self, agent_name: AgentName) -> dict[str, str]:
        agent_list = self.get_agent_list()
        return agent_list.get(agent_name)


    def create_agent(self, agent_name: AgentName, **kwargs) -> Agent:
        data = self.get_agent_config(agent_name=agent_name)
        return Agent(
            role=data['role'],
            backstory=data['backstory'],
            goals=data['goals'],
            **kwargs
        )


class TaskCreation:
    _task_list: dict[str, str] | None = None

    @classmethod
    def get_task_list(cls) -> dict[str, str]:
        if not cls._task_list:
            cls._task_list = YamlLoader().tasks_list
        return cls._task_list

    def get_task_config(self, task_name: TaskName):
        task_list = self.get_task_list()
        return task_list.get(task_name)

    def create_task(self, task_name: TaskName, agent_assigned: Agent, **kwargs) -> Task:
        data = self.get_task_config(task_name=task_name)
        return Task(
            description=data['description'],
            expected_output=data['expected_output'],
            agent=agent_assigned,
            **kwargs
        )

