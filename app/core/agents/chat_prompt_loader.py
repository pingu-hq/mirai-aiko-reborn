from pathlib import Path
from functools import lru_cache
import tomllib
from typing import Any, Literal
from yaml import safe_load as yaml_load




@lru_cache(maxsize=1)
def load_prompt_yaml(filename: str) -> dict:
    config_path = Path(__file__).parent / "config" / filename
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml_load(f)

PHASE_1 = "first_phase"
PHASE_2 = "second_phase"
LILY_SYSTEM_PROMPT = "system_prompt"
LILY_USER_TEMPLATE = "user_template"

class ChatPromptLoader:
    _config_yaml = load_prompt_yaml(filename="chat_prompts.yaml")

    def __init__(self, filename: str = "chat_prompts.yaml"):
        self._config = load_prompt_yaml(filename=filename)

    def get(self, phase: str, prompt: str):
        config_phase = self._config.get(phase, {})
        config_content = config_phase.get(prompt, "")
        return config_content

    @classmethod
    def get_prompts(cls, phase: str, prompt: str):
        config_phase = cls._config_yaml.get(phase, {})
        config_content = config_phase.get(prompt, "")
        return config_content




class ConfigNotInitializedError(RuntimeError):
    def __init__(self, message="Config TOML file must be initialized before use!"):
        super().__init__(message)



class ConfigLoader:
    _config_toml = None

    @classmethod
    def load_toml_config(cls):
        if cls._config_toml is None:
            raise ConfigNotInitializedError()
        return cls._config_toml

    @classmethod
    def init_config_toml_file(cls):
        if cls._config_toml is None:
            config_path = Path(__file__).resolve().parent / "config" / "chat_prompts.toml"
            with open(config_path, "rb") as f:
                cls._config_toml = tomllib.load(f)
        return cls._config_toml


class LilyLoadConfig:

    def __init__(self):
        self._config = ConfigLoader.load_toml_config()

    @property
    def config(self) -> dict[str, Any]:
        return self._config["lily"]

    def first_phase(self, prompt: Literal["system_prompt", "user_prompt"]) -> str:
        return self.config["first-phase"][prompt]
