from fastapi import APIRouter, status, HTTPException
from app.workflows_sandbox.agents_runner import run_agent
from pydantic import BaseModel
from loguru import logger
import json


class CacheMessage:
    _cache: list[dict[str, str]] | None = None

    @classmethod
    def _cache_init(cls) -> list[dict[str, str]]:
        if cls._cache is None:
            cls._cache = []
        return cls._cache


    @property
    def cache(self) -> list[dict[str, str]]:
        return self._cache_init()

    def _add(self, dict_prompt: dict[str, str]) -> None:
        self.cache.append(dict_prompt)

    def add(self, user_msg: str, asst_msg: str) -> None:
        self._add({"user": user_msg, "asst": asst_msg})

    def get(self) -> str:
        return json.dumps(self.cache)


class RequestBody(BaseModel):
    message: str

    

router = APIRouter(
    prefix="/sandbox/api",
    tags=["Sandbox API for the agents"],
)


@router.post("/run-agent")
async def run_agent_endpoint(msg: RequestBody):
    try:
        cm = CacheMessage()
        
        result = await run_agent(
            input_message=msg.message,
            semantic_memory_context="No memory saved yet or user disable semantic memory store",
            most_recent_conversations=cm.get(),
        )

        cm.add(
            user_msg=msg.message,
            asst_msg=result,
        )
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")
    
    
