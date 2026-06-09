from json import dumps

from app.core.state import app_state
from app.services.data.message_vector_services import MessageVectorService
from datetime import datetime
from zoneinfo import ZoneInfo
from asyncio import to_thread
from groq import AsyncGroq
from openai import OpenAI



class AgentService:
    def __init__(self, message_vector_service: MessageVectorService):
        self.message_service = message_vector_service
        self.model_name = "qwen/qwen3-32b"


    @property
    def azure_client(self) -> OpenAI:
        return app_state.azure_client

    @property
    def groq_client(self) -> AsyncGroq:
        return app_state.groq_client

    @property
    def current_datetime(self) -> datetime:
        tz_ph = ZoneInfo('Asia/Manila')
        current_datetime = datetime.now(tz=tz_ph)
        return current_datetime

    async def create_chat_completion(self, messages):
        completions = await self.groq_client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.6,
            max_completion_tokens=22_222,
            top_p=0.95,
            reasoning_effort="default",
            stream=False,
            stop=None,
            reasoning_format="hidden"
        )
        return completions.choices[0].message

    async def full_message_completion(self, user_id: str, content: str):
        previous_context = await self.message_service.retrieve_data_async(
            user_id=user_id,
            content=content
        )
        system_prompt = f"""
        ### SYSTEM:
        You are Nanami, a very sweet and helpful assistant. You will follow what user wants and needs.
        
        ### Instructions:
        The memory context below can be used for User intents, wants and needs. Be sure to stay consistent 
        with the user topic and conversation direction. If context is empty, it means that there's 
        no conversation happened yet between user and assistant
        
        ### Memory Context:
        [{previous_context}]

        ### USER:"""

        user_prompt = f"""<message>{content}</message> <timestamp>{self.current_datetime}</timestamp>"""

        _messages = [{"role":"system", "content":system_prompt},{"role": "user", "content": user_prompt}]

        assistant_prompt = await self.create_chat_completion(_messages)

        raw_memory = [{"role":"user", "content": content},{"role":assistant_prompt.role, "content":assistant_prompt.content}]

        memory_str = dumps(raw_memory)

        await self.message_service.insert_data_async(user_id=user_id, content=memory_str)

        return assistant_prompt.content


