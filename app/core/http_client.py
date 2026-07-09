from httpx import AsyncClient, Client, Limits
from app.core.logger import app_logger


_httpx_sync_client: Client | None = None
_httpx_async_client: AsyncClient | None = None
_limits = Limits(
    max_keepalive_connections=10,
    max_connections=20
)


def init_httpx_sync_client():
    app_logger.info("Starting httpx client!")
    global _httpx_sync_client
    if _httpx_sync_client is None:
        _httpx_sync_client = Client(
            timeout=30.0,
            limits=_limits
        )

def init_httpx_async_client():
    app_logger.info("Starting httpx async client!")
    global _httpx_async_client
    if _httpx_async_client is None:
        _httpx_async_client = AsyncClient(
            timeout=30.0,
            limits=_limits
        )

def close_httpx_sync_client():
    global _httpx_sync_client
    if _httpx_sync_client:
        _httpx_sync_client.close()


async def close_httpx_async_client():
    global _httpx_async_client
    if _httpx_async_client:
        await _httpx_async_client.aclose()
