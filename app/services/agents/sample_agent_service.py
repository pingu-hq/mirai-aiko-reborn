from json import dumps
from datetime import datetime
from zoneinfo import ZoneInfo
from asyncio import to_thread
from groq import AsyncGroq
from openai import OpenAI
from azure.ai.projects import AIProjectClient
from azure.identity import ClientSecretCredential
from app.services.data.message_vector_services import MessageVectorService
from app.core.logger import app_logger
from app.core.local_config import settings




_groq_client: AsyncGroq | None = None
_azure_client: OpenAI | None = None
_azure_ai_project: AIProjectClient | None = None

def init_groq_client():
    global _groq_client
    if _groq_client is None:
        app_logger.info("Starting groq client!")
        _groq_client = AsyncGroq(api_key=settings.groq_api_key.get_secret_value())

def init_azure_ai_project():
    global _azure_ai_project
    if _azure_ai_project is None:
        client_secret_credential = ClientSecretCredential(
            tenant_id=settings.tenant_id.get_secret_value(),
            client_id=settings.client_id.get_secret_value(),
            client_secret=settings.client_secret.get_secret_value(),
        )
        _azure_ai_project = AIProjectClient(
            credential=client_secret_credential,
            endpoint=settings.ai_project_endpoint.get_secret_value()
        )

def init_azure_client():
    if _azure_ai_project:
        global _azure_client
        if _azure_client is None:
            _azure_client = _azure_ai_project.get_openai_client()


async def close_groq_client():
    global _groq_client
    if _groq_client:
        await _groq_client.close()
        _groq_client = None

def close_azure_openai_client():
    global _azure_client
    if _azure_client:
        _azure_client.close()
        _azure_client = None

def close_azure_ai_project():
    global _azure_ai_project
    if _azure_ai_project:
        _azure_ai_project.close()
        _azure_ai_project = None



class AgentService:
    def __init__(self, message_vector_service: MessageVectorService):
        self.message_service = message_vector_service
        self.model_name = "qwen/qwen3-32b"


    @property
    def azure_client(self) -> OpenAI:
        if _azure_client is None:
            raise RuntimeError("Azure client not initialized")
        return _azure_client

    @property
    def groq_client(self) -> AsyncGroq:
        if _groq_client is None:
            raise RuntimeError("Groq client not initialized")
        return _groq_client

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


