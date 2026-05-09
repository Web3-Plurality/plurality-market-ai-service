"""
AWS Bedrock Model Registry
Defines all supported Bedrock models with their configurations and request formats.

NOTE: Many newer models require inference profile IDs (with us./eu./apac. prefix)
instead of direct model IDs. This registry uses US inference profiles for full availability.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict


class ModelProvider(Enum):
    ANTHROPIC = "anthropic"
    META = "meta"
    MISTRAL = "mistral"
    DEEPSEEK = "deepseek"
    AMAZON = "amazon"
    WRITER = "writer"
    OPENAI = "openai"


class RequestFormat(Enum):
    CLAUDE = "claude"
    LLAMA = "llama"
    MISTRAL = "mistral"
    DEEPSEEK = "deepseek"
    NOVA = "nova"
    WRITER = "writer"
    OPENAI = "openai"


@dataclass
class BedrockModelConfig:
    """Configuration for a Bedrock model"""
    model_id: str  # Use inference profile ID (us.xxx) for cross-region support
    provider: ModelProvider
    display_name: str
    description: str
    max_tokens: int
    default_temperature: float
    request_format: RequestFormat


# Complete registry of all supported Bedrock models
# Using US inference profile IDs for maximum availability
BEDROCK_MODELS: Dict[str, BedrockModelConfig] = {
    # ============================================
    # Anthropic Claude Models (using us. inference profiles)
    # ============================================
    "claude-opus-4.5": BedrockModelConfig(
        model_id="us.anthropic.claude-opus-4-5-20251101-v1:0",
        provider=ModelProvider.ANTHROPIC,
        display_name="Claude Opus 4.5",
        description="Most capable Claude model for complex tasks",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.CLAUDE
    ),
    "claude-opus-4.1": BedrockModelConfig(
        model_id="us.anthropic.claude-opus-4-1-20250805-v1:0",
        provider=ModelProvider.ANTHROPIC,
        display_name="Claude Opus 4.1",
        description="Advanced Claude 4 series model",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.CLAUDE
    ),
    # Note: Claude Opus 4 removed - AccessDeniedException on tool calls
    # Note: Claude Sonnet 4.5 removed - AccessDeniedException on tool calls
    "claude-sonnet-4": BedrockModelConfig(
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
        provider=ModelProvider.ANTHROPIC,
        display_name="Claude Sonnet 4",
        description="High capability with good speed",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.CLAUDE
    ),
    "claude-sonnet-3.7": BedrockModelConfig(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        provider=ModelProvider.ANTHROPIC,
        display_name="Claude Sonnet 3.7",
        description="Enhanced reasoning capabilities",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.CLAUDE
    ),
    "claude-sonnet-3.5": BedrockModelConfig(
        model_id="us.anthropic.claude-3-5-sonnet-20240620-v1:0",
        provider=ModelProvider.ANTHROPIC,
        display_name="Claude Sonnet 3.5",
        description="Claude 3.5 Sonnet original",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.CLAUDE
    ),
    "claude-haiku-4.5": BedrockModelConfig(
        model_id="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        provider=ModelProvider.ANTHROPIC,
        display_name="Claude Haiku 4.5",
        description="Fast and efficient responses",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.CLAUDE
    ),
    # Note: Claude Haiku 3 removed - AccessDeniedException on tool calls

    # ============================================
    # Meta Llama Models (using us. inference profiles)
    # Note: Some models removed due to regional access restrictions
    # ============================================
    # Note: Llama 4 Scout/Maverick removed - regional access restrictions
    # Note: Llama 3.2 90B/11B removed - regional access restrictions
    # Note: Llama 3.1 405B removed - regional access restrictions
    "llama-3.3-70b": BedrockModelConfig(
        model_id="us.meta.llama3-3-70b-instruct-v1:0",
        provider=ModelProvider.META,
        display_name="Llama 3.3 70B",
        description="Large 70B parameter model",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.LLAMA
    ),
    "llama-3.2-3b": BedrockModelConfig(
        model_id="us.meta.llama3-2-3b-instruct-v1:0",
        provider=ModelProvider.META,
        display_name="Llama 3.2 3B",
        description="Compact efficient model",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.LLAMA
    ),
    "llama-3.2-1b": BedrockModelConfig(
        model_id="us.meta.llama3-2-1b-instruct-v1:0",
        provider=ModelProvider.META,
        display_name="Llama 3.2 1B",
        description="Lightweight model",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.LLAMA
    ),
    "llama-3.1-70b": BedrockModelConfig(
        model_id="us.meta.llama3-1-70b-instruct-v1:0",
        provider=ModelProvider.META,
        display_name="Llama 3.1 70B",
        description="Large Llama 3.1 model",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.LLAMA
    ),
    "llama-3.1-8b": BedrockModelConfig(
        model_id="us.meta.llama3-1-8b-instruct-v1:0",
        provider=ModelProvider.META,
        display_name="Llama 3.1 8B",
        description="Efficient Llama 3.1 model",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.LLAMA
    ),

    # ============================================
    # Mistral AI Models (using us. inference profiles where available)
    # ============================================
    "mistral-large": BedrockModelConfig(
        model_id="mistral.mistral-large-2402-v1:0",
        provider=ModelProvider.MISTRAL,
        display_name="Mistral Large",
        description="Powerful Mistral model",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.MISTRAL
    ),
    "mistral-large-3": BedrockModelConfig(
        model_id="mistral.mistral-large-3-675b-instruct",
        provider=ModelProvider.MISTRAL,
        display_name="Mistral Large 3 675B",
        description="Largest Mistral model with 675B parameters",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.MISTRAL
    ),
    "mistral-small": BedrockModelConfig(
        model_id="mistral.mistral-small-2402-v1:0",
        provider=ModelProvider.MISTRAL,
        display_name="Mistral Small",
        description="Efficient Mistral model",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.MISTRAL
    ),
    "pixtral-large": BedrockModelConfig(
        model_id="us.mistral.pixtral-large-2502-v1:0",
        provider=ModelProvider.MISTRAL,
        display_name="Pixtral Large",
        description="Vision-capable Mistral model",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.MISTRAL
    ),

    # ============================================
    # DeepSeek Models (using us. inference profiles)
    # ============================================
    "deepseek-r1": BedrockModelConfig(
        model_id="us.deepseek.r1-v1:0",
        provider=ModelProvider.DEEPSEEK,
        display_name="DeepSeek R1",
        description="Advanced reasoning model",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.DEEPSEEK
    ),

    # ============================================
    # Amazon Nova Models (using us. inference profiles)
    # ============================================
    "nova-pro": BedrockModelConfig(
        model_id="us.amazon.nova-pro-v1:0",
        provider=ModelProvider.AMAZON,
        display_name="Nova Pro",
        description="Amazon's pro-tier model",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.NOVA
    ),
    "nova-lite": BedrockModelConfig(
        model_id="us.amazon.nova-lite-v1:0",
        provider=ModelProvider.AMAZON,
        display_name="Nova Lite",
        description="Cost-effective Nova model",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.NOVA
    ),
    "nova-micro": BedrockModelConfig(
        model_id="us.amazon.nova-micro-v1:0",
        provider=ModelProvider.AMAZON,
        display_name="Nova Micro",
        description="Ultra-fast Nova model",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.NOVA
    ),

    # ============================================
    # Writer Models (using us. inference profiles)
    # ============================================
    "palmyra-x4": BedrockModelConfig(
        model_id="us.writer.palmyra-x4-v1:0",
        provider=ModelProvider.WRITER,
        display_name="Palmyra X4",
        description="Enterprise writing model",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.WRITER
    ),
    "palmyra-x5": BedrockModelConfig(
        model_id="us.writer.palmyra-x5-v1:0",
        provider=ModelProvider.WRITER,
        display_name="Palmyra X5",
        description="Advanced enterprise writing model",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.WRITER
    ),

    # ============================================
    # OpenAI GPT-OSS Models (open-weight via Bedrock)
    # ============================================
    "gpt-oss-120b": BedrockModelConfig(
        model_id="openai.gpt-oss-120b-1:0",
        provider=ModelProvider.OPENAI,
        display_name="GPT-OSS 120B",
        description="Large reasoning model (117B params, matches o4-mini)",
        max_tokens=4096,
        default_temperature=0.7,
        request_format=RequestFormat.OPENAI
    ),
    # Note: GPT-OSS 20B removed - limited capability with tool calling
}


def get_model_config(model_key: str) -> BedrockModelConfig:
    """Get model configuration by key"""
    if model_key not in BEDROCK_MODELS:
        raise ValueError(f"Unknown Bedrock model: {model_key}")
    return BEDROCK_MODELS[model_key]


def is_bedrock_model(model_key: str) -> bool:
    """Check if a model key refers to a Bedrock model"""
    return model_key in BEDROCK_MODELS


def get_all_model_keys() -> list:
    """Get all available Bedrock model keys"""
    return list(BEDROCK_MODELS.keys())


def get_models_by_provider(provider: ModelProvider) -> Dict[str, BedrockModelConfig]:
    """Get all models for a specific provider"""
    return {
        key: config
        for key, config in BEDROCK_MODELS.items()
        if config.provider == provider
    }
