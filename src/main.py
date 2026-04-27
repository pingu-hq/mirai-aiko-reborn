from fastapi import FastAPI
import asyncio

app = FastAPI()
@app.get("/")
async def root():
    await asyncio.sleep(1)
    return {"message": "Hello World"}


if __name__ == "__main__":
    import uvicorn
    print("RUNNING UVICORN")
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )