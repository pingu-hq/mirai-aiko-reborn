from datetime import timedelta
from typing import Literal
from app.services.agents.llm_clients import get_groq_async_client
from app.services.data.memory_service import AsyncMemZeroMemoryService
from jinja2 import Template
from cachetools import TTLCache
from asyncio import Lock as AsyncLock
from app.core.agents.chat_prompt_loader import (
ChatPromptLoader,
PHASE_1,
LILY_SYSTEM_PROMPT,
LILY_USER_TEMPLATE)
from app.core.logger import app_logger


_user_template: Template | None = None
_messages_cache: TTLCache | None = None
_async_lock = AsyncLock()


def init_message_cache():
    global _messages_cache
    if _messages_cache is None:
        _messages_cache = TTLCache(maxsize=100, ttl=timedelta(hours=5).total_seconds())




class LilyToolsService:
    def __init__(self):
        self.mem = AsyncMemZeroMemoryService()
        self.groq_client = get_groq_async_client()

    async def web_search(self, user_input: str) -> str:
        completion = await self.groq_client.chat.completions.create(
            model="groq/compound-mini",
            messages=[
                {
                    "role": "user",
                    "content": user_input
                }
            ],
            temperature=1,
            max_completion_tokens=8192,
            top_p=1,
            stop=None,
            compound_custom={
                "tools": {
                    "enabled_tools": [
                        "web_search",
                        "code_interpreter",
                        "visit_website"
                    ]
                }
            }
        )
        web_results = completion.choices[0].message
        app_logger.debug(f"WEB_RESULTS: \n{web_results}")
        return web_results.content

    async def add_memory(self, user_input: str, user_id: str):
        await self.mem.add_memory(user_id=user_id, content=user_input)


class LilyChatRouterService:
    def __init__(self, tools: LilyToolsService):
        self._tools = tools
        self.mem = AsyncMemZeroMemoryService()
        self.groq_client = get_groq_async_client()

    @property
    def ttl_cache(self) -> TTLCache:
        return _messages_cache



    @staticmethod
    async def finalize_user_content(
            user_input: str,
            memory_context: dict,
            recent_conversation: list,
    ) -> str:
        global _user_template
        if _user_template is None:
            user_prompt_template = ChatPromptLoader.get_prompts(phase=PHASE_1, prompt=LILY_USER_TEMPLATE)
            _user_template = Template(
                source=user_prompt_template, enable_async=True
            )
        return await _user_template.render_async(
            user_input=user_input,
            memory_context=memory_context,
            recent_conversation=recent_conversation
        )

    async def add_messages_cache(self, user_id: str, user_msg: str, assistant_msg: str):
        _user = {"role": "user", "content": user_msg}
        _assistant = {"role": "assistant", "content": assistant_msg}

        async with _async_lock:
            messages: list = self.ttl_cache.get(user_id, [])
            messages.append(_user)
            messages.append(_assistant)

            limit = 10
            if len(messages) > limit:
                messages = messages[-limit:]

            self.ttl_cache[user_id] = messages
            return messages

    def get_messages_cache(self, user_id: str):
        return list(self.ttl_cache.get(user_id, []))

    async def gpt_oss_120b(
            self,
            system_content: str,
            user_content: str,
            reasoning_effort: Literal["none", "low", "medium", "high"] = "low"
    ) -> str:
        completion = await self.groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": system_content
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ],
            temperature=.2,
            max_completion_tokens=10_000,
            top_p=1,
            reasoning_effort=reasoning_effort,
            response_format={"type": "json_object"},
        )
        return completion.choices[0].message.content

    async def run(self, user_id: str, user_input: str):
        memory_context = await self.mem.raw_search_memory(
            user_id=user_id,
            query=user_input,
            explain=True,
            output="raw"
        )
        app_logger.debug(f"Internal memory_context: {memory_context}")
        recent_conversation = self.get_messages_cache(user_id=user_id)
        app_logger.debug(f"Internal recent conversation: {recent_conversation}")
        user_content = await self.finalize_user_content(
            user_input=user_input,
            memory_context=memory_context,
            recent_conversation=recent_conversation
        )
        app_logger.debug(f"Finalized user content: {user_content}")
        system_prompt = ChatPromptLoader.get_prompts(phase=PHASE_1, prompt=LILY_SYSTEM_PROMPT)
        response = await self.gpt_oss_120b(
            system_content=system_prompt,
            user_content=user_content
        )
        app_logger.debug(f"Chat completion response: {response}")
        return response

        app_logger.debug(f"Finalized user content: {user_content}")

        response = await self.gpt_oss_120b(
            system_content=SYSTEM_PROMPT,
            user_content=user_content
        )
        app_logger.debug(f"Chat completion response: {response}")
        return response