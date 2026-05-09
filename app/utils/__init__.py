"""
Utility functions for the agent service
"""

from .file_utils import (
    validate_file_type,
    get_markdown_loader,
    get_text_loader_with_encoding,
    create_fallback_text_loader,
    get_json_loader,
    get_loader_for_file_type
)

from .text_utils import (
    normalize_chat_history,
    estimate_tokens,
    calculate_metadata_bytes,
    chunk_content_by_bytes,
    get_chunk_sort_key,
    trim_to_complete_sentences,
    parse_llm_response,
    parse_query_data_response
)

from .chat_history_utils import (
    optimize_chat_history
)

from .llm_utils import (
    extract_title_and_description,
    extract_insights_and_summary,
    separate_query_and_data,
    check_context_relevance,
    check_prompt_language,
    generate_optimized_llm_prompt
)

__all__ = [
    # File utilities
    'validate_file_type',
    'get_markdown_loader',
    'get_text_loader_with_encoding',
    'create_fallback_text_loader',
    'get_json_loader',
    'get_loader_for_file_type',
    # Text utilities
    'normalize_chat_history',
    'estimate_tokens',
    'calculate_metadata_bytes',
    'chunk_content_by_bytes',
    'get_chunk_sort_key',
    'trim_to_complete_sentences',
    'parse_llm_response',
    'parse_query_data_response',
    # Chat history utilities
    'optimize_chat_history',
    # LLM utilities
    'extract_title_and_description',
    'extract_insights_and_summary',
    'separate_query_and_data',
    'check_context_relevance',
    'check_prompt_language',
    'generate_optimized_llm_prompt'
]

