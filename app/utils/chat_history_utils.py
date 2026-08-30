"""
Chat history optimization utilities
"""

from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from app.utils.text_utils import normalize_chat_history, estimate_tokens


async def optimize_chat_history(
    llm: Any,
    chat_history: List, 
    max_tokens: int = 4000,
    preserve_recent_turns: int = 3,
    total_tokens_used: dict = None
) -> dict:
    """
    Optimize chat history using hybrid approach to stay within token limits
    while preserving conversation context.
    
    Strategy (based on research & best practices):
    1. Always keep the most recent N turns (short-term memory)
    2. Summarize middle-aged messages (compression)
    3. Extract key facts/entities from older messages (semantic memory)
    4. Use token-aware truncation
    
    Args:
        llm: LLM instance to use for summarization
        chat_history: List of chat messages
        max_tokens: Maximum tokens to allocate for chat history
        preserve_recent_turns: Number of recent conversation turns to keep verbatim
        total_tokens_used: Token usage tracking dictionary (updated in-place)
        
    Returns:
        dict with optimized_history, summary, and metadata
    """
    if not chat_history:
        return {
            "optimized_messages": [],
            "formatted_history": "",
            "summary": None,
            "total_tokens": 0,
            "optimization_applied": False,
            "total_tokens_used": total_tokens_used
        }
    
    # Normalize chat history to standard format
    normalized_messages = normalize_chat_history(chat_history)
    
    
    # Calculate current token usage
    full_history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in normalized_messages])
    current_tokens = estimate_tokens(full_history_text)
    
    print(f"[CHAT_OPTIMIZER] Total messages: {len(normalized_messages)}, Estimated tokens: {current_tokens}, Max allowed: {max_tokens}")
    
    # If within limits, return as-is
    if current_tokens <= max_tokens:
        print(f"[CHAT_OPTIMIZER] No optimization needed - within token limit")
        return {
            "optimized_messages": normalized_messages,
            "formatted_history": full_history_text,
            "summary": None,
            "total_tokens": current_tokens,
            "optimization_applied": False,
            "total_tokens_used": total_tokens_used
        }
    
    print(f"[CHAT_OPTIMIZER] Optimization required - applying hybrid strategy")
    
    # Strategy: Keep recent + summarize old
    # Calculate how many recent messages to keep (preserve_recent_turns * 2 for user+assistant pairs)
    recent_count = min(preserve_recent_turns * 2, len(normalized_messages))
    recent_messages = normalized_messages[-recent_count:] if recent_count > 0 else []
    older_messages = normalized_messages[:-recent_count] if len(normalized_messages) > recent_count else []
    
    # Calculate tokens for recent messages
    recent_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])
    recent_tokens = estimate_tokens(recent_text)
    
    print(f"[CHAT_OPTIMIZER] Keeping {len(recent_messages)} recent messages ({recent_tokens} tokens)")
    
    # Check if we need to summarize older messages
    summary = None
    available_tokens_for_summary = max_tokens - recent_tokens - 500  # Reserve 500 for buffer
    
    if older_messages and available_tokens_for_summary > 200:
        print(f"[CHAT_OPTIMIZER] Summarizing {len(older_messages)} older messages")
        
        # Create text from older messages
        older_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in older_messages])
        
        system_message = SystemMessage(content="""You are a conversation summarization specialist.

                        Your task:
                        - Extract key facts, decisions, and conclusions
                        - Identify important entities (names, places, concepts)
                        - Capture user preferences and context
                        - Note unresolved questions or ongoing topics

                        Output:
                        - Provide a structured summary in 2-3 paragraphs
                        - Maintain essential context for conversation continuity
                        - Be concise but preserve critical information""")

        human_message = HumanMessage(content=f"""Summarize the following conversation history:
                        {older_text}
                        Create a concise summary that captures the essential context needed to continue this conversation naturally.""")

        try:
            summary_response = await llm.ainvoke([system_message, human_message])
            
            if total_tokens_used and hasattr(summary_response, 'usage_metadata') and summary_response.usage_metadata:
                usage = summary_response.usage_metadata
                input_tokens = usage.get('input_tokens', 0)
                output_tokens = usage.get('output_tokens', 0)
                total_tokens_used["input_tokens"] += input_tokens
                total_tokens_used["output_tokens"] += output_tokens
                total_tokens_used["total_tokens"] += input_tokens + output_tokens
            
            # .text flattens content blocks (list under langchain-core >=1).
            summary = summary_response.text
            summary_tokens = estimate_tokens(summary)
            
            print(f"[CHAT_OPTIMIZER] Summary created ({summary_tokens} tokens)")
            
            # Check if summary + recent fits
            total_tokens_with_summary = recent_tokens + summary_tokens
            
            if total_tokens_with_summary > max_tokens:
                # Truncate summary if needed
                max_summary_chars = (max_tokens - recent_tokens - 100) * 4
                summary = summary[:max_summary_chars] + "..."
                print(f"[CHAT_OPTIMIZER] Summary truncated to fit token limit")
            
        except Exception as e:
            print(f"[CHAT_OPTIMIZER] Failed to create summary: {str(e)}")
            summary = "Previous conversation context available but summarization failed."
    
    # Build optimized history
    optimized_messages = recent_messages.copy()
    
    # Format the final history
    formatted_parts = []
    if summary:
        formatted_parts.append(f"=== Previous Conversation Summary ===\n{summary}\n")
    
    formatted_parts.append("=== Recent Conversation ===")
    for msg in recent_messages:
        formatted_parts.append(f"{msg['role'].title()}: {msg['content']}")
    
    formatted_history = "\n\n".join(formatted_parts)
    final_tokens = estimate_tokens(formatted_history)
    
    print(f"[CHAT_OPTIMIZER] Optimization complete - Final tokens: {final_tokens} (reduced from {current_tokens})")
    
    return {
        "optimized_messages": optimized_messages,
        "formatted_history": formatted_history,
        "summary": summary,
        "total_tokens": final_tokens,
        "optimization_applied": True,
        "original_message_count": len(normalized_messages),
        "kept_message_count": len(recent_messages),
        "summarized_message_count": len(older_messages),
        "total_tokens_used": total_tokens_used
    }

