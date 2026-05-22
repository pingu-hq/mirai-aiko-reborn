from groq import Groq, AsyncGroq
from src.core.local_config import settings

groq_client: Groq | None = None
groq_async_client: AsyncGroq | None = None

class WebSearchTool:
    def __init__(self, reconnect: bool = False):
        if reconnect:
            global groq_client, groq_async_client
            groq_client = None
            groq_async_client = None

    @property
    def groq_conn(self):
        global groq_client
        if groq_client is None:
            groq_client = Groq(api_key=settings.groq_api_key.get_secret_value())
        return groq_client

    @property
    def agroq_conn(self):
        global groq_async_client
        if groq_async_client is None:
            groq_async_client = AsyncGroq(api_key=settings.groq_api_key.get_secret_value())
        return groq_async_client

    @staticmethod
    def _groq_params():
        return {
            "temperature": 0.3,
            "max_completion_tokens": 8192,
            "top_p": 1,
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

    @staticmethod
    def _add_message(input_message: str | list[dict]):

        if isinstance(input_message, str):
            new_input = [{"role": "user", "content": input_message}]
        else:
            new_input = input_message

        return {"messages": new_input}

    def compound_mini_params(self, message):
        model = {"model": "groq/compound-mini"}
        messages = self._add_message(message)
        params = self._groq_params()
        return {**model, **messages, **params}

    def compound_params(self, message):
        model = {"model": "groq/compound"}
        messages = self._add_message(message)
        params = self._groq_params()
        return {**model, **messages, **params}

    def params_to_completions(self, **params):
        conn = self.groq_conn
        result = conn.chat.completions.create(
            **params
        )
        return result.choices[0].message

    async def params_to_completions_async(self, **params):
        conn = self.agroq_conn
        result = await conn.chat.completions.create(
            **params
        )
        return result.choices[0].message

    def web_search_mini(self, message, is_content: bool = True):
        result = self.params_to_completions(**self.compound_mini_params(message))
        if is_content:
            return result.content

        return result

    async def web_search_mini_async(self, message, is_content: bool = True):
        result = await self.params_to_completions_async(**self.compound_mini_params(message))
        if is_content:
            return result.content

        return result
