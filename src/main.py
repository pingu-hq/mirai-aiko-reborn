# from agentic_logic.tools.groq_web_search_tool import (
#     lifespan_context_groq_sync,
#     lifespan_context_groq_async
# )
# from data_storage.all_vector_database_connections.main_milvus_client import (
#     lifespan_context_message_index,
#     lifespan_context_character_index
# )
# from src.agentic_workflows.run_workflow import lifespan_context_azure_client
# from fastapi import FastAPI
# from fastapi.concurrency import asynccontextmanager
# from routers.auth import router as auth_router
# from routers.chatbot import router as chat_router
# import asyncio
#
#
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     app.state.groq_sync = lifespan_context_groq_sync()
#     app.state.groq_async = lifespan_context_groq_async()
#     app.state.character_index = lifespan_context_character_index()
#     app.state.message_index = lifespan_context_message_index()
#     app.state.azure_client = lifespan_context_azure_client()
#     yield
#
#     app.state.groq_sync = None
#     app.state.groq_async = None
#     app.state.character_index = None
#     app.state.message_index = None
#     app.state.azure_client = None
#
# app = FastAPI(lifespan=lifespan)
#
# app.include_router(auth_router)
# app.include_router(chat_router)
#
# @app.get("/hello-env-var")
# async def hello_world():
#     await asyncio.sleep(1)
#     from src.core.local_config import settings
#     return {"message": settings.hello_world}
#
#
#
# if __name__ == "__main__":
#     import uvicorn
#     print("RUNNING UVICORN")
#     uvicorn.run(
#         "src.main:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=False
#     )




# from fastapi import FastAPI
# from routers.auth_v1 import router
#
#
# app = FastAPI()
# app.include_router(router)
#
#
#
# if __name__ == "__main__":
#     import uvicorn
#     print("RUNNING UVICORN")
#     uvicorn.run(
#         "src.main:app",
#         host="0.0.0.0",
#         port=8000,
#         reload=False
#     )