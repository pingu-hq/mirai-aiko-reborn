from pathlib import Path
from crewai import Agent, Task
from app.core.exceptions import custom_check_runtime
import yaml

agent_config_yaml: dict | None = None
task_config_yaml: dict | None = None


def init_yaml_config_files():
    global agent_config_yaml, task_config_yaml
    if agent_config_yaml is None:
        agent_config_yaml = load_yaml_config("agents.yaml")
    if task_config_yaml is None:
        task_config_yaml = load_yaml_config("tasks.yaml")





def yaml_exception(obj, name_of_file: str, key: str):
    return custom_check_runtime(
        singleton_variable=obj,
        error_detail=f"The {name_of_file} not defined in {key}",
    )

def load_yaml_config(filename: str) -> dict:
    config_path = Path(__file__).parent / 'config' / filename
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def create_agent_from_config(agent_key: str, **overrides ) -> Agent:
    config_yaml = yaml_exception(
        obj=agent_config_yaml,
        name_of_file='agent_config.yaml',
        key=agent_key
    )
    config = config_yaml[agent_key]
    return Agent(**config, **overrides)

def create_task_from_config(task_key: str, **overrides ) -> Task:
    config_yaml = yaml_exception(
        obj=task_config_yaml,
        name_of_file='task_config.yaml',
        key=task_key
    )
    config = config_yaml[task_key]
    return Task(**config, **overrides)
