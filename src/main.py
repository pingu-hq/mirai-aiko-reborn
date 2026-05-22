from agentic_logic.tools.groq_web_search_tool import lifespan_context_groq_sync, lifespan_context_groq_async
from src.data_storage.ingest_file_to_vector_store import lifespan_context_vector_store_index
from fastapi import FastAPI, Response, Request, status, HTTPException
from fastapi.concurrency import asynccontextmanager
from src.routers.auth import router as auth_router
from src.routers.chatbot import router as chat_router
import asyncio


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.groq_sync = lifespan_context_groq_sync()
    app.state.groq_async = lifespan_context_groq_async()
    app.state.vector_store_index = lifespan_context_vector_store_index()
    yield

    app.state.groq_sync = None
    app.state.groq_async = None
    app.state.vector_store_index = None


app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(chat_router)

@app.get("/hello-env-var")
async def hello_world():
    await asyncio.sleep(1)
    from src.core.local_config import settings
    return {"message": settings.hello_world}



if __name__ == "__main__":
    import uvicorn
    print("RUNNING UVICORN")
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )