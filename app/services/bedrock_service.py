"""
AWS Bedrock Service
Handles invocation of AWS Bedrock models with proper request/response formatting per provider.
Supports tool calling for all supported model providers.
"""
import boto3
import json
import logging
import uuid
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool

from app.config.settings import settings
from app.config.bedrock_models import get_model_config, BedrockModelConfig, RequestFormat

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for a given text.
    Uses a rough approximation: 1 token ≈ 4 characters (or ~0.75 words).
    This is based on OpenAI's rule of thumb and works reasonably well for most models.

    Args:
        text: The text to estimate tokens for

    Returns:
        Estimated number of tokens
    """
    if not text:
        return 0
    # Average: 1 token = 4 characters (conservative estimate)
    # This works for English text; other languages may vary
    return max(1, len(text) // 4)


class BedrockService:
    """
    Service for invoking AWS Bedrock models with proper request formatting.
    Handles different request/response formats for each model provider.
    """

    def __init__(self):
        """Initialize Bedrock runtime client"""
        self.bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name=settings.AWS_BEDROCK_REGION,
            aws_access_key_id=settings.AWS_BEDROCK_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_BEDROCK_SECRET_ACCESS_KEY
        )
        logger.info(f"BedrockService initialized with region: {settings.AWS_BEDROCK_REGION}")

    def invoke(
        self,
        model_key: str,
        messages: List[BaseMessage],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> AIMessage:
        """
        Invoke a Bedrock model with the given messages.

        Args:
            model_key: The model identifier key (e.g., "claude-sonnet-3.5v2")
            messages: List of LangChain messages
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            tools: Optional list of tools in Bedrock format

        Returns:
            AIMessage containing the model's response (may include tool_calls)
        """
        try:
            config = get_model_config(model_key)

            # Build request body based on model format
            request_body = self._build_request_body(
                config=config,
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature or config.default_temperature,
                max_tokens=max_tokens or config.max_tokens,
                tools=tools
            )

            logger.info(f"Invoking Bedrock model: {config.model_id}")
            if tools:
                logger.info(f"With {len(tools)} tools available")

            # Invoke the model
            response = self.bedrock_runtime.invoke_model(
                modelId=config.model_id,
                body=json.dumps(request_body)
            )

            # Parse response based on model format (pass messages and system_prompt for token estimation)
            return self._parse_response(config, response, messages, system_prompt)

        except Exception as e:
            logger.error(f"Error invoking Bedrock model {model_key}: {e}")
            raise

    def _build_request_body(
        self,
        config: BedrockModelConfig,
        messages: List[BaseMessage],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Build request body based on model provider format"""

        # All formats now support tools
        format_handlers = {
            RequestFormat.CLAUDE: self._build_claude_request,
            RequestFormat.LLAMA: self._build_llama_request,
            RequestFormat.MISTRAL: self._build_mistral_request,
            RequestFormat.DEEPSEEK: self._build_deepseek_request,
            RequestFormat.NOVA: self._build_nova_request,
            RequestFormat.WRITER: self._build_writer_request,
            RequestFormat.OPENAI: self._build_openai_request,
        }

        handler = format_handlers.get(config.request_format)
        if not handler:
            raise ValueError(f"Unknown request format: {config.request_format}")

        return handler(messages, system_prompt, temperature, max_tokens, tools)

    def _build_claude_request(
        self,
        messages: List[BaseMessage],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Build Claude/Anthropic format request with tool support"""
        formatted_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                # Check if this AI message has tool calls
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    # Build content with tool_use blocks
                    content = []
                    # Add text content if present
                    if msg.content:
                        content.append({"type": "text", "text": msg.content})
                    # Add tool_use blocks
                    for tool_call in msg.tool_calls:
                        content.append({
                            "type": "tool_use",
                            "id": tool_call.get("id", str(uuid.uuid4())),
                            "name": tool_call["name"],
                            "input": tool_call["args"]
                        })
                    formatted_messages.append({"role": "assistant", "content": content})
                else:
                    formatted_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, ToolMessage):
                # Tool results go in a user message with tool_result content
                tool_result = {
                    "type": "tool_result",
                    "tool_use_id": msg.tool_call_id,
                    "content": msg.content
                }
                # Check if last message is already a user message with tool results
                if formatted_messages and formatted_messages[-1]["role"] == "user":
                    last_content = formatted_messages[-1]["content"]
                    if isinstance(last_content, list):
                        last_content.append(tool_result)
                    else:
                        formatted_messages[-1]["content"] = [tool_result]
                else:
                    formatted_messages.append({"role": "user", "content": [tool_result]})
            # SystemMessage is handled separately in Claude

        request = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": formatted_messages
        }

        if system_prompt:
            request["system"] = system_prompt

        # Add tools if provided
        if tools:
            request["tools"] = tools

        return request

    def _build_llama_request(
        self,
        messages: List[BaseMessage],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Build Meta Llama format request with tool support"""
        # Build prompt in Llama chat format
        prompt_parts = []

        # If tools are provided, add them to the system prompt
        effective_system_prompt = system_prompt or ""
        if tools:
            tool_descriptions = self._format_tools_for_prompt(tools)
            effective_system_prompt = f"{effective_system_prompt}\n\n{tool_descriptions}" if effective_system_prompt else tool_descriptions

        if effective_system_prompt:
            prompt_parts.append(f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{effective_system_prompt}<|eot_id|>")

        for msg in messages:
            if isinstance(msg, HumanMessage):
                prompt_parts.append(f"<|start_header_id|>user<|end_header_id|>\n\n{msg.content}<|eot_id|>")
            elif isinstance(msg, AIMessage):
                prompt_parts.append(f"<|start_header_id|>assistant<|end_header_id|>\n\n{msg.content}<|eot_id|>")
            elif isinstance(msg, ToolMessage):
                # Include tool results in the conversation
                prompt_parts.append(f"<|start_header_id|>user<|end_header_id|>\n\nTool Result ({msg.tool_call_id}):\n{msg.content}<|eot_id|>")

        # Add assistant header for response
        prompt_parts.append("<|start_header_id|>assistant<|end_header_id|>\n\n")

        return {
            "prompt": "".join(prompt_parts),
            "max_gen_len": max_tokens,
            "temperature": temperature
        }

    def _build_mistral_request(
        self,
        messages: List[BaseMessage],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Build Mistral format request with native tool support"""
        formatted_messages = []

        # Add system prompt as first message if provided
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})

        # Mistral doesn't allow 'user' role after 'tool' role
        # We need to skip follow-up HumanMessages that come after ToolMessages
        for i, msg in enumerate(messages):
            if isinstance(msg, HumanMessage):
                # Skip if this is a follow-up message after tool results
                # (Check if previous message was a ToolMessage)
                if i > 0 and isinstance(messages[i-1], ToolMessage):
                    # Skip this follow-up instruction as Mistral will automatically continue
                    continue
                formatted_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                # Check if this AI message has tool calls
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    formatted_messages.append({
                        "role": "assistant",
                        "content": msg.content or "",
                        "tool_calls": [
                            {
                                "id": tc.get("id", str(uuid.uuid4())),
                                "type": "function",
                                "function": {
                                    "name": tc["name"],
                                    "arguments": json.dumps(tc["args"])
                                }
                            }
                            for tc in msg.tool_calls
                        ]
                    })
                else:
                    formatted_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, ToolMessage):
                formatted_messages.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "content": msg.content
                })

        request = {
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        # Add tools if provided (Mistral native tool format)
        if tools:
            request["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool.get("input_schema", {"type": "object", "properties": {}})
                    }
                }
                for tool in tools
            ]

        return request

    def _build_deepseek_request(
        self,
        messages: List[BaseMessage],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Build DeepSeek format request.
        DeepSeek R1 on AWS Bedrock uses a simple prompt-based format (not messages array).
        Note: DeepSeek R1 does NOT support native tool calling, so we use prompt injection.
        """
        # Build prompt by combining system prompt, tool descriptions, and messages
        prompt_parts = []

        # Add system prompt
        if system_prompt:
            prompt_parts.append(f"System: {system_prompt}")

        # Add tool descriptions if provided (prompt-based tool injection)
        if tools:
            tool_descriptions = self._format_tools_for_prompt(tools)
            prompt_parts.append(tool_descriptions)

        # Add conversation messages
        for msg in messages:
            if isinstance(msg, HumanMessage):
                prompt_parts.append(f"User: {msg.content}")
            elif isinstance(msg, AIMessage):
                prompt_parts.append(f"Assistant: {msg.content}")
            elif isinstance(msg, ToolMessage):
                prompt_parts.append(f"Tool Result ({msg.tool_call_id}): {msg.content}")

        # Add assistant prefix for response
        prompt_parts.append("Assistant:")

        return {
            "prompt": "\n\n".join(prompt_parts),
            "max_tokens": min(max_tokens, 8192),  # DeepSeek R1 quality degrades above 8192
            "temperature": temperature
        }

    def _build_nova_request(
        self,
        messages: List[BaseMessage],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Build Amazon Nova format request with native tool support"""
        formatted_messages = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted_messages.append({
                    "role": "user",
                    "content": [{"text": msg.content}]
                })
            elif isinstance(msg, AIMessage):
                # Check for tool calls
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    content = []
                    if msg.content:
                        content.append({"text": msg.content})
                    for tc in msg.tool_calls:
                        content.append({
                            "toolUse": {
                                "toolUseId": tc.get("id", str(uuid.uuid4())),
                                "name": tc["name"],
                                "input": tc["args"]
                            }
                        })
                    formatted_messages.append({"role": "assistant", "content": content})
                else:
                    formatted_messages.append({
                        "role": "assistant",
                        "content": [{"text": msg.content}]
                    })
            elif isinstance(msg, ToolMessage):
                formatted_messages.append({
                    "role": "user",
                    "content": [{
                        "toolResult": {
                            "toolUseId": msg.tool_call_id,
                            "content": [{"text": msg.content}]
                        }
                    }]
                })

        request = {
            "messages": formatted_messages,
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": temperature
            }
        }

        if system_prompt:
            request["system"] = [{"text": system_prompt}]

        # Add tools if provided (Nova native format)
        if tools:
            request["toolConfig"] = {
                "tools": [
                    {
                        "toolSpec": {
                            "name": tool["name"],
                            "description": tool["description"],
                            "inputSchema": {
                                "json": tool.get("input_schema", {"type": "object", "properties": {}})
                            }
                        }
                    }
                    for tool in tools
                ]
            }

        return request

    def _build_writer_request(
        self,
        messages: List[BaseMessage],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Build Writer Palmyra format request with tool support"""
        formatted_messages = []

        # If tools are provided, add them to the system prompt (prompt injection for models without native tool support)
        effective_system_prompt = system_prompt or ""
        if tools:
            tool_descriptions = self._format_tools_for_prompt(tools)
            effective_system_prompt = f"{effective_system_prompt}\n\n{tool_descriptions}" if effective_system_prompt else tool_descriptions

        if effective_system_prompt:
            formatted_messages.append({"role": "system", "content": effective_system_prompt})

        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                formatted_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, ToolMessage):
                # Include tool results as user message
                formatted_messages.append({
                    "role": "user",
                    "content": f"Tool Result ({msg.tool_call_id}):\n{msg.content}"
                })

        return {
            "messages": formatted_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

    def _format_tools_for_prompt(self, tools: List[Dict[str, Any]]) -> str:
        """
        Format tools as text description for models without native tool support.
        This allows models to understand and use tools through prompt engineering.
        Uses forceful language to ensure smaller models comply with tool usage.
        """
        tool_text = """IMPORTANT: You have access to the following tools. You MUST use them when appropriate.

CRITICAL INSTRUCTIONS:
1. If the user's message contains a URL (http:// or https://), you MUST call the extract_url_content tool FIRST before responding.
2. If the user asks about current events, news, weather, or real-time information, you MUST call the web_search tool.
3. When you need to use a tool, respond with ONLY a JSON object in this exact format (no other text):
{"tool_call": {"name": "tool_name", "arguments": {"arg1": "value1"}}}

Available tools:
"""
        for tool in tools:
            tool_text += f"\n- {tool['name']}: {tool['description']}"
            if tool.get("input_schema", {}).get("properties"):
                props = tool["input_schema"]["properties"]
                required = tool["input_schema"].get("required", [])
                tool_text += "\n  Parameters:"
                for prop_name, prop_def in props.items():
                    req_str = " (required)" if prop_name in required else " (optional)"
                    tool_text += f"\n    - {prop_name}: {prop_def.get('description', prop_def.get('type', 'string'))}{req_str}"

        tool_text += """

REMEMBER:
- If URL is in the query → output {"tool_call": {"name": "extract_url_content", "arguments": {"url": "the_url_here"}}}
- If asking about current/real-time info → output {"tool_call": {"name": "web_search", "arguments": {"query": "search terms"}}}
- Output ONLY the JSON object when using a tool, nothing else."""
        return tool_text

    def _parse_response(self, config: BedrockModelConfig, response, messages: List[BaseMessage] = None, system_prompt: str = None) -> AIMessage:
        """Parse response based on model provider format"""
        response_body = json.loads(response['body'].read())

        # Each format has its own handler for tool call support
        parse_handlers = {
            RequestFormat.CLAUDE: self._parse_claude_response,
            RequestFormat.LLAMA: self._parse_llama_response,
            RequestFormat.MISTRAL: self._parse_mistral_response,
            RequestFormat.DEEPSEEK: self._parse_deepseek_response,
            RequestFormat.NOVA: self._parse_nova_response,
            RequestFormat.WRITER: self._parse_writer_response,
            RequestFormat.OPENAI: self._parse_openai_response,
        }

        handler = parse_handlers.get(config.request_format)
        if not handler:
            raise ValueError(f"Unknown response format: {config.request_format}")

        ai_message = handler(response_body)

        # Extract token usage from response and attach to AIMessage
        # Different model families use different usage formats:
        # - Claude: usage.input_tokens / usage.output_tokens (snake_case)
        # - Llama: prompt_token_count / generation_token_count (top-level fields)
        # - Nova: usage.inputTokens / usage.outputTokens (camelCase)
        # - OpenAI GPT-OSS: usage.prompt_tokens / usage.completion_tokens
        # - Mistral: No usage data in response
        # - Writer/DeepSeek: Uses one of the above formats

        input_tokens = 0
        output_tokens = 0

        # Try Claude format first (most common)
        usage = response_body.get('usage', {})
        if usage and ('input_tokens' in usage or 'inputTokens' in usage or 'prompt_tokens' in usage):
            # Try snake_case (Claude)
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)

            # If still 0, try camelCase (Nova)
            if input_tokens == 0 and output_tokens == 0:
                input_tokens = usage.get('inputTokens', 0)
                output_tokens = usage.get('outputTokens', 0)

            # If still 0, try OpenAI format (GPT-OSS)
            if input_tokens == 0 and output_tokens == 0:
                input_tokens = usage.get('prompt_tokens', 0)
                output_tokens = usage.get('completion_tokens', 0)

        # Try Llama format (top-level fields)
        elif 'prompt_token_count' in response_body or 'generation_token_count' in response_body:
            input_tokens = response_body.get('prompt_token_count', 0)
            output_tokens = response_body.get('generation_token_count', 0)

        # If no tokens found from provider, estimate them
        if input_tokens == 0 and output_tokens == 0:
            # Estimate output tokens from AI message content
            output_text = ai_message.content if hasattr(ai_message, 'content') else ""
            output_tokens = estimate_tokens(str(output_text))

            # Estimate input tokens from messages and system prompt
            if messages:
                input_text = ""
                if system_prompt:
                    input_text += system_prompt + " "
                for msg in messages:
                    if hasattr(msg, 'content'):
                        input_text += str(msg.content) + " "
                input_tokens = estimate_tokens(input_text)

        # Attach usage_metadata if we have any token counts (actual or estimated)
        if input_tokens > 0 or output_tokens > 0:
            total_tokens = input_tokens + output_tokens
            ai_message.usage_metadata = {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': total_tokens
            }

        return ai_message

    def _parse_claude_response(self, response_body: Dict[str, Any]) -> AIMessage:
        """Parse Claude response, handling both text and tool_use responses"""
        content_blocks = response_body.get('content', [])

        text_content = ""
        tool_calls = []

        for block in content_blocks:
            block_type = block.get('type', '')

            if block_type == 'text':
                text_content += block.get('text', '')
            elif block_type == 'tool_use':
                tool_calls.append({
                    "id": block.get('id', str(uuid.uuid4())),
                    "name": block.get('name', ''),
                    "args": block.get('input', {})
                })

        if tool_calls:
            logger.info(f"Claude response includes {len(tool_calls)} tool calls")
            return AIMessage(content=text_content, tool_calls=tool_calls)
        return AIMessage(content=text_content)

    def _parse_llama_response(self, response_body: Dict[str, Any]) -> AIMessage:
        """Parse Llama response with potential tool call extraction"""
        import re
        content = response_body.get('generation', '')
        tool_calls = self._extract_tool_calls_from_text(content)
        if tool_calls:
            logger.info(f"Llama response includes {len(tool_calls)} tool calls")
            # Clean up the content to remove the raw JSON tool call
            cleaned_content = content
            if content.strip().startswith('{') and content.strip().endswith('}'):
                cleaned_content = ""
            else:
                patterns = [
                    r'\{\s*"tool_call"\s*:\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*\}',
                    r'\{\s*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:\s*\{[^{}]*\}\s*\}'
                ]
                for pattern in patterns:
                    cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.DOTALL).strip()
            return AIMessage(content=cleaned_content or "I need to search for this information.", tool_calls=tool_calls)
        return AIMessage(content=content)

    def _parse_mistral_response(self, response_body: Dict[str, Any]) -> AIMessage:
        """Parse Mistral response with native tool call support"""
        message = response_body.get('choices', [{}])[0].get('message', {})
        content = message.get('content', '')
        tool_calls = []

        # Check for native tool calls
        if message.get('tool_calls'):
            for tc in message['tool_calls']:
                func = tc.get('function', {})
                tool_calls.append({
                    "id": tc.get('id', str(uuid.uuid4())),
                    "name": func.get('name', ''),
                    "args": json.loads(func.get('arguments', '{}')) if isinstance(func.get('arguments'), str) else func.get('arguments', {})
                })

        if tool_calls:
            logger.info(f"Mistral response includes {len(tool_calls)} tool calls")
            return AIMessage(content=content or "", tool_calls=tool_calls)
        return AIMessage(content=content)

    def _parse_deepseek_response(self, response_body: Dict[str, Any]) -> AIMessage:
        """Parse DeepSeek response with prompt-based tool call extraction"""
        import re
        # DeepSeek R1 returns response in 'choices' array with 'text' field
        choices = response_body.get('choices', [])
        if choices:
            content = choices[0].get('text', '') or choices[0].get('message', {}).get('content', '')
        else:
            # Fallback to direct text field
            content = response_body.get('text', '') or response_body.get('generation', '')

        # Try to extract tool calls from text (prompt-based approach)
        tool_calls = self._extract_tool_calls_from_text(content)
        if tool_calls:
            logger.info(f"DeepSeek response includes {len(tool_calls)} tool calls")
            # Clean up the content to remove the raw JSON tool call
            cleaned_content = content
            if content.strip().startswith('{') and content.strip().endswith('}'):
                cleaned_content = ""
            else:
                patterns = [
                    r'\{\s*"tool_call"\s*:\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*\}',
                    r'\{\s*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:\s*\{[^{}]*\}\s*\}'
                ]
                for pattern in patterns:
                    cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.DOTALL).strip()
            return AIMessage(content=cleaned_content or "I need to search for this information.", tool_calls=tool_calls)
        return AIMessage(content=content)

    def _parse_nova_response(self, response_body: Dict[str, Any]) -> AIMessage:
        """Parse Amazon Nova response with native tool call support"""
        message = response_body.get('output', {}).get('message', {})
        content_blocks = message.get('content', [])

        text_content = ""
        tool_calls = []

        for block in content_blocks:
            if 'text' in block:
                text_content += block['text']
            elif 'toolUse' in block:
                tu = block['toolUse']
                tool_calls.append({
                    "id": tu.get('toolUseId', str(uuid.uuid4())),
                    "name": tu.get('name', ''),
                    "args": tu.get('input', {})
                })

        if tool_calls:
            logger.info(f"Nova response includes {len(tool_calls)} tool calls")
            return AIMessage(content=text_content, tool_calls=tool_calls)
        return AIMessage(content=text_content)

    def _parse_writer_response(self, response_body: Dict[str, Any]) -> AIMessage:
        """Parse Writer response with potential tool call extraction"""
        import re
        content = response_body.get('choices', [{}])[0].get('message', {}).get('content', '')
        tool_calls = self._extract_tool_calls_from_text(content)
        if tool_calls:
            logger.info(f"Writer response includes {len(tool_calls)} tool calls")
            # Clean up the content to remove the raw JSON tool call
            cleaned_content = content
            if content.strip().startswith('{') and content.strip().endswith('}'):
                cleaned_content = ""
            else:
                patterns = [
                    r'\{\s*"tool_call"\s*:\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*\}',
                    r'\{\s*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:\s*\{[^{}]*\}\s*\}'
                ]
                for pattern in patterns:
                    cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.DOTALL).strip()
            return AIMessage(content=cleaned_content or "I need to search for this information.", tool_calls=tool_calls)
        return AIMessage(content=content)

    def _extract_tool_calls_from_text(self, content: str) -> List[Dict[str, Any]]:
        """
        Extract tool calls from text content for models using prompt-based tool calling.
        Looks for JSON objects with tool_call structure.
        """
        import re
        tool_calls = []

        # First, try to parse the entire content as JSON (model might output just the JSON)
        try:
            content_stripped = content.strip()
            if content_stripped.startswith('{') and content_stripped.endswith('}'):
                parsed = json.loads(content_stripped)
                if 'tool_call' in parsed:
                    tc = parsed['tool_call']
                    tool_calls.append({
                        "id": str(uuid.uuid4()),
                        "name": tc.get('name', ''),
                        "args": tc.get('arguments', {})
                    })
                    return tool_calls
                elif 'name' in parsed and 'arguments' in parsed:
                    tool_calls.append({
                        "id": str(uuid.uuid4()),
                        "name": parsed['name'],
                        "args": parsed['arguments']
                    })
                    return tool_calls
        except json.JSONDecodeError:
            pass

        # Try to find JSON tool call patterns using regex
        # Pattern for {"tool_call": {"name": "...", "arguments": {...}}}
        pattern = r'\{\s*"tool_call"\s*:\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*\}'
        matches = re.findall(pattern, content, re.DOTALL)

        for match in matches:
            try:
                parsed = json.loads(match)
                if 'tool_call' in parsed:
                    tc = parsed['tool_call']
                    tool_calls.append({
                        "id": str(uuid.uuid4()),
                        "name": tc.get('name', ''),
                        "args": tc.get('arguments', {})
                    })
            except json.JSONDecodeError:
                continue

        # Also try pattern for {"name": "...", "arguments": {...}}
        if not tool_calls:
            pattern2 = r'\{\s*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:\s*\{[^{}]*\}\s*\}'
            matches2 = re.findall(pattern2, content, re.DOTALL)
            for match in matches2:
                try:
                    parsed = json.loads(match)
                    tool_calls.append({
                        "id": str(uuid.uuid4()),
                        "name": parsed['name'],
                        "args": parsed['arguments']
                    })
                except json.JSONDecodeError:
                    continue

        return tool_calls

    def _build_openai_request(
        self,
        messages: List[BaseMessage],
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Build OpenAI GPT-OSS format request.
        GPT-OSS models use OpenAI-compatible chat completion format.
        Note: GPT-OSS models are text-only (no native tool calling).
        We use prompt-based tool injection.
        """
        formatted_messages = []

        # If tools are provided, inject them into the system prompt
        effective_system_prompt = system_prompt or ""
        if tools:
            tool_descriptions = self._format_tools_for_prompt(tools)
            effective_system_prompt = f"{effective_system_prompt}\n\n{tool_descriptions}" if effective_system_prompt else tool_descriptions

        if effective_system_prompt:
            formatted_messages.append({"role": "system", "content": effective_system_prompt})

        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                formatted_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, ToolMessage):
                # Include tool results as user message
                formatted_messages.append({
                    "role": "user",
                    "content": f"Tool Result ({msg.tool_call_id}):\n{msg.content}"
                })

        return {
            "messages": formatted_messages,
            "max_completion_tokens": max_tokens,
            "temperature": temperature
        }

    def _parse_openai_response(self, response_body: Dict[str, Any]) -> AIMessage:
        """Parse OpenAI GPT-OSS response with prompt-based tool call extraction"""
        # GPT-OSS returns response in OpenAI chat completion format
        choices = response_body.get('choices', [])
        if choices:
            content = choices[0].get('message', {}).get('content', '')
        else:
            content = ''

        # Remove any <reasoning>...</reasoning> tags from the content
        # GPT-OSS may include reasoning wrapped in these tags
        import re
        content = re.sub(r'<reasoning>.*?</reasoning>', '', content, flags=re.DOTALL).strip()

        # Try to extract tool calls from text (prompt-based approach)
        tool_calls = self._extract_tool_calls_from_text(content)
        if tool_calls:
            logger.info(f"OpenAI GPT-OSS response includes {len(tool_calls)} tool calls")
            # When tool calls are found, clean up the content to remove the raw JSON
            # This ensures the conversation history is cleaner for subsequent calls
            cleaned_content = content
            # Try to remove the entire JSON if content is mostly JSON
            if content.strip().startswith('{') and content.strip().endswith('}'):
                cleaned_content = ""
            else:
                # Remove embedded JSON patterns
                patterns = [
                    r'\{\s*"tool_call"\s*:\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}\s*\}',
                    r'\{\s*"name"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:\s*\{[^{}]*\}\s*\}'
                ]
                for pattern in patterns:
                    cleaned_content = re.sub(pattern, '', cleaned_content, flags=re.DOTALL).strip()
            return AIMessage(content=cleaned_content or "I need to search for this information.", tool_calls=tool_calls)
        return AIMessage(content=content)


# Create singleton instance
bedrock_service = BedrockService()
