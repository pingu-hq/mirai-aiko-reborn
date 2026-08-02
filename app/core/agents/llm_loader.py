from typing import Literal
from crewai import LLM
from cachetools import TTLCache
from app.core.local_config import settings
from threading import Lock




_LLM_HOLDER: TTLCache | None = None
_LLM_LOCK = Lock()



def init_crewai_llm_cache():
    global _LLM_HOLDER
    if _LLM_HOLDER is None:
        _LLM_HOLDER = TTLCache(maxsize=15, ttl=3600)

def close_crewai_llm_cache():
    global _LLM_HOLDER
    if _LLM_HOLDER:
        _LLM_HOLDER.expire()
        _LLM_HOLDER.clear()


class LLMLoader:
    def __init__(self):
        self.api_key = settings.groq_api_key.get_secret_value()

    def groq_config(self):
        return {
            "base_url": "https://api.groq.com/openai/v1",
            "api_key": self.api_key,
        }

    @staticmethod
    def llm_builder(key: str, **kwargs) -> LLM:
        kwargs.setdefault(
            "top_p", 1)
        kwargs.setdefault(
            "temperature", 0.5)
        kwargs.setdefault(
            "max_completion_tokens", 8_000)
        global _LLM_HOLDER
        if _LLM_HOLDER is not None and key in _LLM_HOLDER:
            return _LLM_HOLDER[key]

        with _LLM_LOCK:
            if _LLM_HOLDER is None:
                init_crewai_llm_cache()

            assert _LLM_HOLDER is not None

            if key not in _LLM_HOLDER:
                _LLM_HOLDER[key] = LLM(**kwargs)

            return _LLM_HOLDER[key]

    def get_groq_llm(
            self,
            model: Literal["small", "big"],
            reasoning_effort: Literal["none", "low", "medium", "high"] | None = None,
            max_completion_tokens=10_000,
            **kwargs
    ):
        if model == "small":
            gpt_oss_model = "groq/openai/gpt-oss-20b"
        else:
            gpt_oss_model = "groq/openai/gpt-oss-120b"

        cache_key = f"{model}:{reasoning_effort}:{max_completion_tokens}"
        return self.llm_builder(
            key=cache_key,
            model=gpt_oss_model,
            reasoning_effort=reasoning_effort,
            max_completion_tokens=max_completion_tokens,
            **self.groq_config(),
            **kwargs
        )
