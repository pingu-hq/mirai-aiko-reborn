from typing import Literal
from crewai import LLM
from cachetools import TTLCache
from app.core.local_config import settings
from threading import Lock




class LLMLoader:
    _llm_holder: TTLCache | None = None
    _llm_lock = Lock()

    @property
    def groq_config(self):
        return {
            "base_url": "https://api.groq.com/openai/v1",
            "api_key": settings.groq_api_key.get_secret_value(),
        }

    @classmethod
    def llm_builder(cls, key: str, **kwargs) -> LLM:
        kwargs.setdefault(
            "top_p", 1)
        kwargs.setdefault(
            "temperature", 0.5)
        kwargs.setdefault(
            "max_completion_tokens", 8_000)

        if cls._llm_holder is not None and key in cls._llm_holder:
            return cls._llm_holder[key]

        with cls._llm_lock:
            if cls._llm_holder is None:
                cls.init_crewai_llm_cache()

            assert cls._llm_holder is not None

            if key not in cls._llm_holder:
                cls._llm_holder[key] = LLM(**kwargs)
            return cls._llm_holder[key]


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
            **self.groq_config,
            **kwargs
        )

    @classmethod
    def init_crewai_llm_cache(cls):
        if cls._llm_holder is None:
            cls._llm_holder = TTLCache(maxsize=15, ttl=3600)

    @classmethod
    def close_crewai_llm_cache(cls):
        if cls._llm_holder:
            cls._llm_holder.expire()
            cls._llm_holder.clear()
            cls._llm_holder = None