from openai import AsyncOpenAI, OpenAI
from core.local_config import settings
from fastapi import Request
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(Path(__file__).parent.parent.parent.resolve(True) / "secrets" / "agent_configs.txt")

def load_azure_client():
    params = {
        "base_url" : settings.azure_endpoint.get_secret_value(),
        "api_key" : settings.azure_api_key.get_secret_value()
    }
    client_async = AsyncOpenAI(**params)
    client_sync = OpenAI(**params)

    return client_async, client_sync



def lifespan_context_azure_llm():
    return load_azure_client()[1]

def basic_llm_run(request: Request, content: str):
    client = request.app.state.azure_llm
    completion = client.chat.completions.create(
        model=os.environ["LLM_TYPE_A"],
        messages=[
            {
                "role": "user",
                "content": content,
            }
        ],
    )

    return completion.choices[0].message.content
