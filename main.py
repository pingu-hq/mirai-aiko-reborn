from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.repositories.caches import RedisCacheBaseRepository
from app.repositories.database import MongoBase
from app.routers.auth_router import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    RedisCacheBaseRepository.init_redis_cache_repository()
    MongoBase.init_mongo_client()
    yield
    await RedisCacheBaseRepository.close_redis_cache_repository()
    await MongoBase.close_mongo_client()

app = FastAPI(
    version="0.1.0",
    title="Mirai Aiko (Reborn Version)",
    lifespan=lifespan,
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
