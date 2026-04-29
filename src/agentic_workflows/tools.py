from groq import Groq, AsyncGroq
from src.core.local_config import settings

groq_client: Groq | None = None
groq_async_client: AsyncGroq | None = None


def connection(reconnect: bool = False):
    global groq_client, groq_async_client
    if reconnect:
        groq_client = None
        groq_async_client = None

    if groq_client is None:
        groq_client = Groq(api_key=settings.groq_api_key.get_secret_value())

    if groq_async_client is None:
        groq_async_client = AsyncGroq(api_key=settings.groq_api_key.get_secret_value())

    return groq_client, groq_async_client

def groq_params():
    return {
        "temperature": 0.3,
        "max_completion_tokens":8192,
        "top_p":1,
        "stream": False,
        "stop": None,
        "compound_custom": {
            "tools": {
                "enabled_tools": [
                    "web_search",
                    "visit_website"
                ]
            }
        }
    }

def add_message(input_message: str | list[dict]):

    if isinstance(input_message, str):
        new_input = [{"role":"user","content":input_message}]
    else:
        new_input = input_message

    return {"messages":new_input}

def compound_mini_params(message):
    model = {"model":"groq/compound-mini"}
    messages = add_message(message)
    params = groq_params()
    return {**model, **messages, **params}

def compound_params(message):
    model = {"model":"groq/compound"}
    messages = add_message(message)
    params = groq_params()
    return {**model, **messages, **params}

def params_to_completions(**params):
    conn, _ = connection()
    result = conn.chat.completions.create(
        **params
    )
    return result.choices[0].message

async def params_to_completions_async(**params):
    _, conn = connection()
    result = await conn.chat.completions.create(
        **params
    )
    return result.choices[0].message

def web_search_mini(message, is_content: bool = True):
    result = params_to_completions(**compound_mini_params(message))
    if is_content:
        return result.content

    return result

async def web_search_mini_async(message, is_content: bool = True):
    result = params_to_completions_async(**compound_mini_params(message))
    if is_content:
        return result.content

    return result