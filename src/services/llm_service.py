from langchain.chat_models import init_chat_model
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

from src.config import settings

import os
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY


class LLMService:
    """A class for interacting with a language model (LLM)."""

    def __init__(self):
        # Initialize any required resources, e.g., loading models or setting up configurations
        pass

    async def ask_openai_llm(
        self, prompt: ChatPromptTemplate, model_name: str = "gpt-4o-mini", output_schema: type = None,
    ) -> any:
        """Send a prompt to the OpenAI LLM and return the response."""
        return await self._ask_llm(prompt, model_name, model_provider="openai", output_schema=output_schema)

    async def _ask_llm(
        self,
        prompt: ChatPromptTemplate,
        model_name: str,
        model_provider: str,
        output_schema: type = None,
        **kwargs,
    ) -> any:
        """Send a prompt to the LLM and return the response."""
        llm = init_chat_model(model_name, model_provider=model_provider, )
        structured_llm = llm.with_structured_output(output_schema) if output_schema else llm
        response = structured_llm.invoke(prompt, **kwargs)
        return response

    def format_prompt(self, system_message: str, user_message: str, **kwargs) -> str:
        """Format the prompt with system and user messages."""
        system_prompt = SystemMessagePromptTemplate.from_template(system_message)
        user_prompt = HumanMessagePromptTemplate.from_template(user_message)
        chat_prompt = ChatPromptTemplate.from_messages([system_prompt, user_prompt])
        return chat_prompt.format(**kwargs)
