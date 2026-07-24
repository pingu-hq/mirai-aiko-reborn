from datetime import timedelta
from typing import Literal
from app.services.agents.llm_clients import get_groq_async_client
from app.services.data.memory_service import AsyncMemZeroMemoryService
from jinja2 import Template
from cachetools import TTLCache
from asyncio import Lock as AsyncLock
from app.core.logger import app_logger


_user_template: Template | None = None
_messages_cache: TTLCache | None = None
_async_lock = AsyncLock()


def init_message_cache():
    global _messages_cache
    if _messages_cache is None:
        _messages_cache = TTLCache(maxsize=100, ttl=timedelta(hours=5).total_seconds())



SYSTEM_PROMPT = """
You are an intelligent intent router for an advanced AI assistant. Your task is to analyze the provided inputs—consisting of the user's current input, relevant memory context, and recent conversation history—and output a strict JSON object with two boolean decision flags.

### INPUTS:
- user_input: The raw text input provided by the user.
- memory_context: Relevant background memories retrieved via search.
- recent_conversation: The 5 most recent turns of dialogue between the user and the assistant.

### OUTPUT FORMAT:
You must output ONLY a valid JSON object matching this exact schema, with no markdown code blocks around it if required by your JSON mode, or standard JSON format:
{
  "search_web": true/false,
  "add_memory": true/false
}

### DECISION GUIDELINES:
1. "search_web": 
   - Set to `true` if the user is asking for a translation, requesting real-time/current information, asking about external facts not guaranteed to be in static training data, or if the query drifts from or requires verification against the provided context.
   - Set to `false` if the query can be fully answered using general knowledge or existing memory/conversation context.

2. "add_memory": 
   - Set to `true` if the `user_input` contains a distinct personal fact, preference, detail about the user's life, or a direct instruction that is valuable to store for future interactions.
   - Set to `false` if the input is a general question, a casual remark, a command, or already well-documented.

Analyze the inputs carefully and return only the requested JSON."""


class LilyChatRouterService:
    def __init__(self):
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
            _user_template = Template(
                source="""### USER:
                - USER_INPUT: {{user_input}}
                - MEMORY_CONTEXT: {{memory_context}}
                - RECENT_CONVERSATION: {{recent_conversation}}
                """, enable_async=True
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

        response = await self.gpt_oss_120b(
            system_content=SYSTEM_PROMPT,
            user_content=user_content
        )
        app_logger.debug(f"Chat completion response: {response}")
        return response