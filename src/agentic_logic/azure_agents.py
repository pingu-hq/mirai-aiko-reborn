from azure.ai.projects import AIProjectClient
from azure.identity import ClientSecretCredential
from asyncio import to_thread
from pydantic import SecretStr
from functools import lru_cache
from src.core.local_config import settings
from abc import ABC, abstractmethod




@lru_cache()
def azure_openai_loader():
    cred = ClientSecretCredential(
        tenant_id=settings.tenant_id.get_secret_value(),
        client_id=settings.client_id.get_secret_value(),
        client_secret=settings.client_secret.get_secret_value(),
    )
    client = AIProjectClient(
        credential=cred,
        endpoint=settings.ai_project_endpoint.get_secret_value()
    )
    return client.get_openai_client()




class AgentBaseClass(ABC):
    def __init__(self, agent_config: SecretStr, input_message: str | list[dict[str, str]]):
        self.agent_config = agent_config
        self._input_message = input_message

    @property
    def input_user_prompt(self):
        return {"input":self._input_message}

    def _agent_reference_parser(self):
        normal_string = self.agent_config.get_secret_value()
        name, version = normal_string.split("||")
        return name, version


    @staticmethod
    def _extra_body_template(name, version):
        return {
            "extra_body": {
                "agent_reference": {
                    "name":name,
                    "version":version,
                    "type": "agent_reference"
                }
            }
        }

    @property
    def extra_body(self):
        agent_ref = self._agent_reference_parser()
        return self._extra_body_template(*agent_ref)

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    async def aexecute(self):
        pass




class MiraiAikoAgent(AgentBaseClass):
    def __init__(self, input_message: str | list[dict[str, str]]):
        super().__init__(agent_config=settings.temp_first_agent,input_message=input_message)
        self.message = input_message
        self.client = azure_openai_loader()


    def execute(self):
        try:
            completion = self.client.responses.create(
                **self.input_user_prompt,
                **self.extra_body
            )
            return completion.output_text
        except Exception as ex:
            raise ex

    async def aexecute(self):
        try:
            return await to_thread(self.execute)
        except Exception as ex:
            raise ex