from typing import Dict, List, Optional
from langchain.chat_models import init_chat_model
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

from src.constants import StructureOutputPrompt
from src.config import settings

import os

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
os.environ["TAVILY_API_KEY"] = settings.TAVILY_API_KEY


class LLMService:
    """A class for interacting with a language model (LLM)."""

    def __init__(self):
        # Initialize any required resources, e.g., loading models or setting up configurations
        pass

    async def ask_openai_llm(
        self,
        prompt: ChatPromptTemplate,
        model_name: str = "gpt-4o-mini",
        output_schema: type = None,
    ) -> any:
        """Send a prompt to the OpenAI LLM and return the response."""
        return await self._ask_llm(
            prompt, model_name, model_provider="openai", output_schema=output_schema
        )

    async def _ask_llm(
        self,
        prompt: ChatPromptTemplate,
        model_name: str,
        model_provider: str,
        output_schema: type = None,
        **kwargs,
    ) -> any:
        """Send a prompt to the LLM and return the response."""
        llm = init_chat_model(
            model_name,
            model_provider=model_provider,
        )
        structured_llm = (
            llm.with_structured_output(output_schema) if output_schema else llm
        )
        response = structured_llm.invoke(prompt, **kwargs)
        return response

    def format_prompt(
        self,
        system_message: str,
        user_message: str,
        additional_content: Optional[List[Dict]] = None,
        **kwargs,
    ) -> str:
        """Format the prompt with system and user messages."""
        system_prompt = SystemMessagePromptTemplate.from_template(system_message)
        user_prompt = HumanMessagePromptTemplate.from_template(user_message)
        chat_prompt = ChatPromptTemplate.from_messages([system_prompt, user_prompt])
        # Format messages with kwargs substitution
        messages = chat_prompt.format_messages(**kwargs)
        if additional_content:
            last_msg = messages[-1]
            if isinstance(last_msg, HumanMessage):
                if isinstance(last_msg.content, str) or not last_msg.content:
                    last_msg.content = [{"type": "text", "text": last_msg.content}]
                last_msg.content.extend(additional_content)
                messages[-1] = last_msg
        return messages

    async def ask_search_agent(
        self,
        prompt: ChatPromptTemplate,
        model_name: str,
        model_provider: str,
        output_schema: type = None,
    ):
        model = init_chat_model(model=model_name, model_provider=model_provider)
        search = TavilySearch(max_results=2)
        tools = [search]
        agent_executor = create_react_agent(model=model, tools=tools)
        response = agent_executor.invoke({"messages": prompt})
        if output_schema:
            agent_output = response["messages"][-1].content
            structured_agent_response = await self._structure_agent_response(
                agent_output=agent_output, output_schema=output_schema
            )
            return structured_agent_response
        return response["messages"][-1].content

    async def _structure_agent_response(self, agent_output: str, output_schema: type):
        formatted_prompt = self.format_prompt(
            system_message=StructureOutputPrompt.SYSTEM_PROMPT,
            user_message=StructureOutputPrompt.USER_PROMPT,
            agent_output=agent_output,
            format_instructions=output_schema.model_json_schema(),
        )
        return await self.ask_openai_llm(prompt=formatted_prompt, output_schema=output_schema)
