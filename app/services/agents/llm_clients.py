from app.core.local_config import settings
from groq import AsyncGroq


_groq_client_async: AsyncGroq | None = None



def init_groq_client():
    global _groq_client_async
    if _groq_client_async is None:
        _groq_client_async = AsyncGroq(
            api_key=settings.groq_api_key.get_secret_value(),
        )


async def close_groq_client():
    global _groq_client_async
    if _groq_client_async:
        await _groq_client_async.close()
