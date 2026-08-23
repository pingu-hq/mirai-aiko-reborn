from fastapi import FastAPI

app = FastAPI(
    version="0.1.0",
    title="Mirai Aiko (Reborn Version)",
)


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