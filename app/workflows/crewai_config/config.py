from pathlib import Path
from tomllib import load
from typing import Literal


def _to_path(dir_name: Literal["agents", "tasks"], file_name: str) -> Path:
    return Path(__file__).resolve().parent / f"{dir_name}/{file_name}"


CONTEXT_SYNTHESIZER_AGENT_CONFIG = _to_path("agents", "context_synthesizer.toml")
CONTEXT_AND_INTENT_ANALYSIS_TASK_CONFIG = _to_path("tasks", "context_and_intent_analysis.toml")
FINAL_RESPONSE_GENERATION_TASK_CONFIG = _to_path("tasks", "final_response_generation.toml")



def load_agent_config(agent_config: Path, version: str = "latest") -> dict[str, str] | None:
    try:
        with open(agent_config, "rb") as f:
            full_config = load(f)
            return full_config.get(version, None)
    except FileNotFoundError:
        return None