"""
LLM Factory
Factory pattern for obtaining the correct LLM based on model selection.
Routes between Gemini (default) and Bedrock models.
"""
import asyncio
import logging
from typing import List, Optional, Any, Dict
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.settings import settings
from app.config.bedrock_models import is_bedrock_model
from app.services.bedrock_service import bedrock_service

logger = logging.getLogger(__name__)


class BedrockLLMWrapper:
    """
    Wrapper to make BedrockService compatible with LangChain LLM interface.
    Provides invoke/ainvoke methods matching the ChatGoogleGenerativeAI interface.
    Supports tool calling for all Bedrock model providers.
    """

    def __init__(self, model_key: str):
        self.model_key = model_key
        self._tools: List[Any] = []
        self._bedrock_tools: List[Dict[str, Any]] = []

    def _convert_langchain_tools_to_bedrock(self, tools: List[Any]) -> List[Dict[str, Any]]:
        """
        Convert LangChain tools to Bedrock tool format.
        This format is used across all providers (each provider's handler adapts it as needed).

        LangChain tool schema -> Bedrock tool format:
        {
            "name": "tool_name",
            "description": "Tool description",
            "input_schema": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
        """
        bedrock_tools = []

        for tool in tools:
            try:
                # Get tool schema from LangChain tool
                if hasattr(tool, 'get_input_schema'):
                    schema = tool.get_input_schema().schema()
                elif hasattr(tool, 'args_schema') and tool.args_schema:
                    schema = tool.args_schema.schema()
                else:
                    # Fallback for simple tools
                    schema = {"type": "object", "properties": {}, "required": []}

                # Extract properties and required fields
                properties = schema.get('properties', {})
                required = schema.get('required', [])

                # Clean up properties (remove titles, etc.)
                clean_properties = {}
                for prop_name, prop_def in properties.items():
                    clean_prop = {
                        "type": prop_def.get('type', 'string'),
                        "description": prop_def.get('description', f'The {prop_name} parameter')
                    }
                    clean_properties[prop_name] = clean_prop

                bedrock_tool = {
                    "name": tool.name,
                    "description": tool.description or f"Tool: {tool.name}",
                    "input_schema": {
                        "type": "object",
                        "properties": clean_properties,
                        "required": required
                    }
                }
                bedrock_tools.append(bedrock_tool)
                logger.info(f"Converted tool '{tool.name}' to Bedrock format")

            except Exception as e:
                logger.warning(f"Failed to convert tool {getattr(tool, 'name', 'unknown')}: {e}")
                continue

        return bedrock_tools

    def invoke(self, messages: List[BaseMessage], **kwargs) -> AIMessage:
        """Synchronous invoke with tool support for all models"""
        system_prompt = kwargs.get("system_prompt")

        # Pass tools to all models - BedrockService handles the format per provider
        tools_to_use = self._bedrock_tools if self._bedrock_tools else None

        if tools_to_use:
            logger.info(f"Invoking Bedrock model {self.model_key} with {len(tools_to_use)} tools")

        return bedrock_service.invoke(
            model_key=self.model_key,
            messages=messages,
            system_prompt=system_prompt,
            tools=tools_to_use
        )

    async def ainvoke(self, messages: List[BaseMessage], **kwargs) -> AIMessage:
        """Async invoke - runs sync invoke in executor"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.invoke(messages, **kwargs)
        )

    def bind_tools(self, tools: List[Any]):
        """
        Bind tools to the LLM.
        Converts LangChain tools to Bedrock format for all model providers.
        """
        self._tools = tools
        self._bedrock_tools = self._convert_langchain_tools_to_bedrock(tools)
        logger.info(f"Converted {len(self._bedrock_tools)} tools for Bedrock model {self.model_key}")
        return self

    def with_structured_output(self, schema: Any):
        """
        Return a runnable that outputs structured data.
        Note: Limited support for Bedrock - returns self for compatibility.
        """
        return self


class LLMFactory:
    """
    Factory for obtaining the correct LLM based on model selection.
    Maintains singleton instances of Gemini models for efficiency.
    """

    def __init__(self):
        # Initialize Gemini models (lazy loading)
        self._gemini_default = None
        self._gemini_advanced = None
        self._gemini_3_pro = None

    @property
    def gemini_default(self):
        """Lazy-loaded Gemini 2.0 Flash"""
        if self._gemini_default is None:
            self._gemini_default = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash",
                api_key=settings.GOOGLE_API_KEY,
                temperature=0.7,
                max_output_tokens=32768
            )
        return self._gemini_default

    @property
    def gemini_advanced(self):
        """Lazy-loaded Gemini 2.5 Flash"""
        if self._gemini_advanced is None:
            self._gemini_advanced = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                api_key=settings.GOOGLE_API_KEY,
                temperature=0.7,
                max_output_tokens=32768
            )
        return self._gemini_advanced

    @property
    def gemini_3_pro(self):
        """Lazy-loaded Gemini 3 Pro Preview"""
        if self._gemini_3_pro is None:
            self._gemini_3_pro = ChatGoogleGenerativeAI(
                model="gemini-3-pro-preview",
                api_key=settings.GOOGLE_API_KEY,
                temperature=0.7,
                max_output_tokens=32768,
                include_thoughts=True
            )
        return self._gemini_3_pro

    def get_llm(self, model_key: str = "gemini"):
        """
        Get the appropriate LLM for the given model key.

        Args:
            model_key: The model identifier. "gemini" returns the default Gemini model.
                      Other keys are looked up in the Bedrock model registry.

        Returns:
            LLM instance (ChatGoogleGenerativeAI or BedrockLLMWrapper)
        """
        # Handle Gemini models
        if model_key == "gemini" or model_key == "gemini-2.5-flash":
            logger.info(f"Using Gemini 2.5 Flash (default)")
            return self.gemini_advanced
        elif model_key == "gemini-2.0-flash":
            logger.info(f"Using Gemini 2.0 Flash")
            return self.gemini_default
        elif model_key == "gemini-3-pro":
            logger.info(f"Using Gemini 3 Pro")
            return self.gemini_3_pro
        elif model_key.startswith("gemini"):
            # Fallback for any other gemini variant
            logger.info(f"Using Gemini 2.5 Flash for key: {model_key}")
            return self.gemini_advanced

        # Handle Bedrock models
        if is_bedrock_model(model_key):
            logger.info(f"Using Bedrock model: {model_key}")
            return BedrockLLMWrapper(model_key)

        # Default fallback to Gemini
        logger.warning(f"Unknown model key '{model_key}', falling back to Gemini 2.5 Flash")
        return self.gemini_advanced

    def get_llm_for_agentic(self, model_key: str = "gemini"):
        """
        Get LLM specifically for agentic workflows.
        Uses Gemini 3 Pro for Gemini, or BedrockLLMWrapper for Bedrock models.

        Args:
            model_key: The model identifier

        Returns:
            LLM instance suitable for agentic workflows
        """
        return self.get_llm(model_key)


# Create singleton factory instance
llm_factory = LLMFactory()
