from fastapi import FastAPI
import asyncio

app = FastAPI()
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