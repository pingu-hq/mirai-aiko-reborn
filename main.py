from fastapi import FastAPI

from app.routers.auth_router import router as auth_router

app = FastAPI(
    version="0.1.0",
    title="Mirai Aiko (Reborn Version)",
)

app.include_router(auth_router, prefix="/api/auth", tags=["Auth for users with sample user test"])


@app.get("/health-check")
def health_check():
    return {"status": "ok", "message": "Hello World"}





if __name__ == "__main__":
    import uvicorn
    print("RUNNING UVICORN")
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=False
    )
