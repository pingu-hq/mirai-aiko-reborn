from typing import Any, Literal
from crewai import Crew, Process, LLM, Flow
from crewai.crew import CrewStreamingOutput, CrewOutput
from cachetools import TTLCache
from app.core.agents.agent_loader import AgentLoader,SampleAgentLoader
from app.core.local_config import settings
from threading import Lock
import os


# Disables CrewAI from phoning home with anonymous usage data
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

# Disables the annoying 20-second terminal prompt asking to view traces
os.environ["CREWAI_TRACING_ENABLED"] = "false"

# (Optional) The nuclear option: disables ALL OpenTelemetry globally
# Only use this if you aren't using OpenTelemetry for anything else!
os.environ["OTEL_SDK_DISABLED"] = "true"



_llm_cache: TTLCache | None = None
_cache_lock = Lock()


def base_llm():
    return {
        "base_url":"https://api.groq.com/openai/v1",
        "max_completion_tokens":10_000, "temperature":.5,
        "api_key":settings.groq_api_key.get_secret_value(),    "top_p":1,
    }


def get_gpt_oss_llm(model: str, reasoning_effort: Literal["none", "low", "medium", "high"] | None = None) -> LLM:
    key = f"{model}:{reasoning_effort}"
    with _cache_lock:
        if key not in _llm_cache:
            _llm_cache[key] = LLM(
                model=model,
                reasoning_effort=reasoning_effort,
                **base_llm()
            )
        return _llm_cache[key]




small_llm = lambda: get_gpt_oss_llm(model="groq/openai/gpt-oss-20b", reasoning_effort="medium")
large_llm = lambda: get_gpt_oss_llm(model="groq/openai/gpt-oss-120b", reasoning_effort="medium")


def init_cache_and_crew_llms():
    global _llm_cache
    if _llm_cache is None:
        _llm_cache = TTLCache(maxsize=10, ttl=3600)

def close_cache_and_crew_llms():
    global _llm_cache
    if _llm_cache:
        _llm_cache.expire()
        _llm_cache.clear()


class CrewFactory:
    def __init__(self):
        self._agent_loader = None
        self._loader = None

    @property
    def agent_loader(self) -> AgentLoader:
        if self._agent_loader is None:
            self._agent_loader = AgentLoader()
        return self._agent_loader

    @property
    def loader(self) -> SampleAgentLoader:
        if self._loader is None:
            self._loader = SampleAgentLoader()
        return self._loader

    def build_crew(self, **kwargs):
        params = self.agent_loader.agents_and_tasks_as_params()
        return Crew(
            **params,
            process=Process.sequential,
            verbose=True,
            **kwargs
        )

    def create_agent_llm(
            self,
            model: Literal["small","big"],
            reasoning_effort: Literal["none", "low", "medium", "high"] | None = None,
            max_completion_tokens: int = 10_000,
            temperature: float = .5,

    ):
        global _llm_cache

        llm_params = {
            "base_url":"https://api.groq.com/openai/v1",
            "api_key":settings.groq_api_key.get_secret_value(),
            "top_p":1,
        }

        cache_key = f"{model}:{reasoning_effort}:{max_completion_tokens}"
        with _cache_lock:
            if cache_key not in _llm_cache:
                _llm_cache[cache_key] = LLM(
                    model=model,
                    reasoning_effort=reasoning_effort,
                    max_completion_tokens=max_completion_tokens,
                    temperature=temperature,
                    **llm_params
                )
            return _llm_cache[cache_key]

    def run(self, inputs: dict[str, Any] | None = None,**kwargs) -> str:
        _crew_instance = self.build_crew(**kwargs)
        results = _crew_instance.kickoff(inputs=inputs) if inputs else _crew_instance.kickoff()
        return results.raw

    async def run_async(self, inputs: dict[str, Any] | None = None, **kwargs) -> str:
        _crew_instance = self.build_crew(**kwargs)
        results = await _crew_instance.kickoff_async(inputs=inputs) if inputs else await _crew_instance.kickoff_async()
        return results.raw


class CrewFactoryVersion1:
    def __init__(self):
        self._loader = None

    @property
    def loader(self) -> SampleAgentLoader:
        if self._loader is None:
            self._loader = SampleAgentLoader()
        return self._loader

    def build_crew(self, **kwargs):
        kwargs.setdefault("verbose", True)
        kwargs.setdefault("process", Process.sequential)
        params = self.loader.agents_and_tasks_as_params()
        return Crew(
            **params,
            **kwargs
        )

    def create_agent_llm(
            self,
            model: Literal["small","big"],
            reasoning_effort: Literal["none", "low", "medium", "high"] | None = None,
            max_completion_tokens: int = 10_000,
            temperature: float = .5,

    ):
        global _LLM_HOLDER
        if model == "small":
            gpt_oss_model = "groq/openai/gpt-oss-20b"
        else:
            gpt_oss_model = "groq/openai/gpt-oss-120b"

        llm_params = {
            "base_url":"https://api.groq.com/openai/v1",
            "api_key":settings.groq_api_key.get_secret_value(),
            "top_p":1,
        }

        cache_key = f"{model}:{reasoning_effort}:{max_completion_tokens}"
        with _cache_lock:
            if cache_key not in _llm_cache:
                _llm_cache[cache_key] = LLM(
                    model=gpt_oss_model,
                    reasoning_effort=reasoning_effort,
                    max_completion_tokens=max_completion_tokens,
                    temperature=temperature,
                    **llm_params
                )
            return _llm_cache[cache_key]

    def run(self, inputs: dict[str, Any] | None = None,**kwargs) -> str:
        _crew_instance = self.build_crew(**kwargs)
        results = _crew_instance.kickoff(inputs=inputs) if inputs else _crew_instance.kickoff()
        return results.raw

    async def run_async(self, inputs: dict[str, Any] | None = None, **kwargs) -> CrewOutput | CrewStreamingOutput:
        _crew_instance = self.build_crew(**kwargs)
        return await _crew_instance.kickoff_async(inputs=inputs)
