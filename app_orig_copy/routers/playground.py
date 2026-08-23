from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.auth.opaque_auth_service import OpaqueAuthService
from app.services.data.memory_service import AsyncMemZeroMemoryService
from app.core.agents.llm_loader import LLMLoader
from app.dependencies.auth import get_opaque_auth_service
from logger import app_logger
from crewai.tools import tool
from crewai import Agent, Task, Crew, Process
from app.services.agents.lily_chat_service import LilyChatRouterService
import json

from crewai.tools import BaseTool
from pydantic import PrivateAttr




router = APIRouter(
    prefix="/api/playground", tags=["Sandbox and playground to test routers."]
)

llm_loader = LLMLoader()
llm = llm_loader.get_groq_llm("big","medium")

@tool("semantic_search")
async def semantic_search(user_id: str, user_input: str) -> str:
    """
    Search the user's memory semantically.

    Args:
        user_id: User identifier.
        user_input: Search query.

    Returns:
        Relevant semantic search results.
    """
    m = AsyncMemZeroMemoryService()
    result = await m.search_memory(
        user_id=user_id,
        content=user_input
    )
    return result


@tool("get_all_messages")
async def get_all_messages(user_id: str) -> str:
    """
    Retrieve the user's recent conversation history.

    Args:
        user_id: User identifier.

    Returns:
        Most recent messages first.
    """
    m = AsyncMemZeroMemoryService()
    results = await m.memory_client.get_all(filters={"user_id": user_id})
    return json.dumps(results)




class SemanticSearchTool(BaseTool):
    name: str = "semantic_search"
    description: str = (
        "Search the user's memory semantically using the current authenticated user."
    )

    _memory_service: AsyncMemZeroMemoryService = PrivateAttr()
    _user_id: str | None = PrivateAttr(default=None)

    def __init__(self):
        super().__init__()
        self._memory_service = AsyncMemZeroMemoryService()

    def set_user(self, user_id: str):
        self._user_id = user_id

    async def _run(self, user_input: str) -> str:
        if self._user_id is None:
            raise ValueError("User ID has not been assigned.")

        return await self._memory_service.search_memory(
            user_id=self._user_id,
            content=user_input,
        )

def agent_1(tools, model):
    return Agent(
        role="Memory Assistant",
        goal=(
            "Answer the user's request primarily through tool usage. "
            "Always decide whether semantic search or recent message retrieval "
            "is appropriate before responding."
        ),
        backstory=(
            "You are responsible for retrieving user memories. "
            "You should rely on tools instead of making assumptions."
        ),
        tools=[tools, get_all_messages],
        verbose=True,
        llm=model
    )
def task_1(agent):
    return Task(
        description="""
            User Input:
            {user_input}

            Determine which tool is most appropriate.

            Use semantic_search when:
            - The user is asking about previous topics.
            - The user asks to remember or search memories.
            - The user references something from earlier.

            Use get_all_messages when:
            - The user asks for recent conversation history.
            - The user wants their latest messages.
            - The request depends on chronological context.

            Do not answer from your own knowledge when a tool can provide better context.
            """,
        expected_output="""
            A concise response based entirely on the information returned by the selected tool(s).
            """,
        agent=agent,
    )

memory_agent = Agent(
    role="Memory Assistant",
    goal=(
        "Answer the user's request primarily through tool usage. "
        "Always decide whether semantic search or recent message retrieval "
        "is appropriate before responding."
    ),
    backstory=(
        "You are responsible for retrieving user memories. "
        "You should rely on tools instead of making assumptions."
    ),
    tools=[
    ],
    verbose=True,
    llm=llm
)

memory_task = Task(
    description="""
        User ID:
        {user_id}
        
        User Input:
        {user_input}
        
        Determine which tool is most appropriate.
        
        Use semantic_search when:
        - The user is asking about previous topics.
        - The user asks to remember or search memories.
        - The user references something from earlier.
        
        Use get_all_messages when:
        - The user asks for recent conversation history.
        - The user wants their latest messages.
        - The request depends on chronological context.
        
        Do not answer from your own knowledge when a tool can provide better context.
        """,
    expected_output="""
        A concise response based entirely on the information returned by the selected tool(s).
        """,
    agent=memory_agent,
)

async def crew_execute(user_id: str, user_input: str):
    _crew = Crew(
        agents=[memory_agent],
        tasks=[memory_task],
        verbose=True,
        process=Process.sequential
    )
    response = await _crew.kickoff_async(inputs={"user_input": user_input, "user_id": user_id})
    return response.raw

async def crew_run(user_id: str, user_input: str):
    groq_llm = llm_loader.get_groq_llm("big", "medium")
    semantic_search_tool = SemanticSearchTool()
    semantic_search_tool.set_user(user_id=user_id)
    first_agent = agent_1(tools=semantic_search_tool, model=groq_llm)
    first_task = task_1(first_agent)
    _crew = Crew(
        agents=[first_agent],
        tasks=[first_task],
        verbose=True,
        process=Process.sequential
    )
    response = await _crew.kickoff_async(inputs={"user_input": user_input})
    return response.raw

class Chat(BaseModel):
    message: str

class MemoryInput(Chat):
    memory_id: str



@router.post("/ask-chat", status_code=status.HTTP_200_OK)
async def ask_chat(
        chat: Chat,
        opaque: OpaqueAuthService = Depends(get_opaque_auth_service),
):
    try:
        user_id = await opaque.get_user_id()
        # response = await crew_run(
        #     user_id=user_id, user_input=chat.message
        # )
        # response = await lily_chat_run(user_id=user_id, user_message=chat.message)
        lily = LilyChatRouterService()
        response = await lily.run(user_id=user_id, user_input=chat.message)
        app_logger.debug(f"Response Endpoint /ask-chat: {response}")
        return {"status":"ok","crewai_result": response}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error endpoint /send-message-to-mirai-aiko : {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request")
