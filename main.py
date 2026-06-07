from fastapi import FastAPI
from app.routers.auth import router as auth_router


app = FastAPI(
    version="0.1.0",
    title="Mirai Aiko (Reborn Version)",
)
app.include_router(auth_router)


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