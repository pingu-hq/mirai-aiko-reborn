from groq import Groq, AsyncGroq
from fastapi import Request
from core.local_config import settings



class GroqClients:
    def __init__(self):
        self.api_key = settings.groq_api_key

    @property
    def groq_sync(self):
        return Groq(api_key=self.api_key.get_secret_value())

    @property
    def groq_async(self):
        return AsyncGroq(api_key=self.api_key.get_secret_value())

def lifespan_context_groq_async():
    return GroqClients().groq_async

def lifespan_context_groq_sync():
    return GroqClients().groq_sync



class WebSearchTool:
    def __init__(self, request: Request):
        self.req = request
        self.groq_sync = request.app.state.groq_sync
        self.groq_async = request.app.state.groq_async


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
        result = self.groq_sync.chat.completions.create(
            **params
        )
        return result.choices[0].message

    async def params_to_completions_async(self, **params):
        result = await self.groq_async.chat.completions.create(
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
