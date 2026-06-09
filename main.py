from fastapi import FastAPI
from app.routers.auth import router as auth_router
from app.routers.chat import router as chat_router
from app.core.lifespan import lifespan


app = FastAPI(
    version="0.1.0",
    title="Mirai Aiko (Reborn Version)",
    lifespan=lifespan
)
app.include_router(auth_router)
app.include_router(chat_router)


@app.get("/health-check")
def health_check():
    return {"status": "ok", "message": "Hello World"}





if __name__ == "__main__":
    import uvicorn
    print("RUNNING UVICORN")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )