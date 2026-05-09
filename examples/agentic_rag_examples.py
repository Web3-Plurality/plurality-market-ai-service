"""
Example usage of the Agentic RAG endpoint

This file demonstrates various scenarios and how the agentic RAG system handles them.
"""

import requests
import json
from typing import Dict, Any


# Configuration
API_BASE_URL = "http://localhost:8000"  # Update with your API URL
API_KEY = "dev-key-12345"  # Default API key (or set CONTEXT_API_KEY in .env)


def call_agentic_rag(
    user_id: str,
    profile_id: str,
    query: str,
    chat_history: list = None,
    context_summary: str = "",
    k: int = 5,
    attach_context_summary: bool = False,
    platform: str = "chatGPT"
) -> Dict[str, Any]:
    """Call the agentic RAG endpoint"""

    url = f"{API_BASE_URL}/rag/agentic-rag-query"
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    # Convert context_summary string to list if needed (API expects List[str])
    if isinstance(context_summary, str):
        context_summary = [context_summary] if context_summary else []

    payload = {
        "userId": user_id,
        "profileId": profile_id,
        "query": query,
        "k": k,
        "chatHistory": chat_history or [],
        "contextSummary": context_summary,
        "attachContextSummary": attach_context_summary,
        "platform": platform
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()


def print_result(result: Dict[str, Any], title: str):
    """Pretty print the result"""
    print(f"\n{'=' * 80}")
    print(f"EXAMPLE: {title}")
    print(f"{'=' * 80}")

    metadata = result.get("workflow_metadata", {})

    print(f"\n📋 Query: {result.get('query')}")
    print(f"\n🔍 Workflow Metadata:")
    print(f"  - Query Type: {metadata.get('query_type')}")
    print(f"  - Language: {metadata.get('language')}")
    print(f"  - Query Expanded: {metadata.get('query_expanded')}")
    print(f"  - Context Relevant: {metadata.get('context_relevant')}")
    print(f"  - Separated Query: {metadata.get('separated_query')}")
    print(f"  - Separated Data: {metadata.get('separated_data')}")

    print(f"\n📊 Results:")
    print(f"  - Contexts Found: {result.get('total_contexts_found')}")
    print(f"  - Sources: {len(result.get('sources', []))}")

    print(f"\n💰 Token Usage:")
    tokens = result.get('tokens_used', {})
    print(f"  - Input: {tokens.get('input_tokens')}")
    print(f"  - Output: {tokens.get('output_tokens')}")
    print(f"  - Total: {tokens.get('total_tokens')}")

    print(f"\n✨ Optimized Prompt (first 200 chars):")
    print(f"  {result.get('optimized_prompt', '')[:200]}...")

    if metadata.get('errors'):
        print(f"\n⚠️ Errors:")
        for error in metadata.get('errors', []):
            print(f"  - {error}")

    print(f"\n{'=' * 80}\n")


# ========== EXAMPLE 1: Simple Query ==========
def example_simple_query():
    """Example of a simple, straightforward query"""

    result = call_agentic_rag(
        user_id="user-123",
        profile_id="profile-456",
        query="What is machine learning?",
        k=3
    )

    print_result(result, "Simple Query")
    # Expected: query_type="simple", no expansion needed


# ========== EXAMPLE 2: Vague Query with Context ==========
def example_vague_query():
    """Example of a vague query that needs expansion"""

    result = call_agentic_rag(
        user_id="user-123",
        profile_id="profile-456",
        query="tell me more about that",
        context_summary="Documents about Python programming and machine learning",
        k=5
    )

    print_result(result, "Vague Query with Context")
    # Expected: query_type="vague", query_expanded=True


# ========== EXAMPLE 3: Conversational Follow-up ==========
def example_conversational_query():
    """Example of a follow-up question in a conversation"""

    chat_history = [
        {"role": "user", "content": "What are the main features of Python?"},
        {"role": "assistant", "content": "Python's main features include: 1) Easy syntax, 2) Dynamic typing, 3) Rich libraries..."},
        {"role": "user", "content": "Can you give examples of popular libraries?"},
        {"role": "assistant", "content": "Popular Python libraries include NumPy, Pandas, TensorFlow, Django, Flask..."}
    ]

    result = call_agentic_rag(
        user_id="user-123",
        profile_id="profile-456",
        query="Which one is best for data science?",
        chat_history=chat_history,
        k=5
    )

    print_result(result, "Conversational Follow-up")
    # Expected: query_type="conversational", uses chat history context


# ========== EXAMPLE 4: Complex Query ==========
def example_complex_query():
    """Example of a complex, multi-part query"""

    result = call_agentic_rag(
        user_id="user-123",
        profile_id="profile-456",
        query="Compare supervised and unsupervised learning, explain their use cases, and provide examples of algorithms for each category",
        k=10
    )

    print_result(result, "Complex Multi-part Query")
    # Expected: query_type="complex", retrieves more contexts (k=10)


# ========== EXAMPLE 5: Query with Data ==========
def example_query_with_data():
    """Example of a query with data/code provided"""

    result = call_agentic_rag(
        user_id="user-123",
        profile_id="profile-456",
        query="Explain this code: \n\ndef factorial(n):\n    if n == 0:\n        return 1\n    return n * factorial(n-1)",
        k=3
    )

    print_result(result, "Query with Data/Code")
    # Expected: separated_data contains the code, separated_query has the question


# ========== EXAMPLE 6: No Profile ID (Skip Retrieval) ==========
def example_no_profile():
    """Example where no profile ID is provided"""

    result = call_agentic_rag(
        user_id="user-123",
        profile_id="",  # No profile ID
        query="What is artificial intelligence?",
        k=5
    )

    print_result(result, "No Profile ID (Skip Retrieval)")
    # Expected: skip_retrieval=True, total_contexts_found=0


# ========== EXAMPLE 7: Multi-language Query ==========
def example_multilanguage_query():
    """Example of a query in a different language"""

    result = call_agentic_rag(
        user_id="user-123",
        profile_id="profile-456",
        query="¿Qué es el aprendizaje automático?",  # Spanish
        k=5
    )

    print_result(result, "Multi-language Query (Spanish)")
    # Expected: language="Spanish", prompt optimized in Spanish


# ========== EXAMPLE 8: Romanized Language ==========
def example_romanized_language():
    """Example of a romanized (non-native script) query"""

    result = call_agentic_rag(
        user_id="user-123",
        profile_id="profile-456",
        query="Machine learning kya hai?",  # Roman Urdu
        k=5
    )

    print_result(result, "Romanized Language Query (Roman Urdu)")
    # Expected: language="Roman Urdu"


# ========== EXAMPLE 9: First Message with Context Summary ==========
def example_first_message_with_context():
    """Example of first message with context summary attached"""

    result = call_agentic_rag(
        user_id="user-123",
        profile_id="profile-456",
        query="Tell me about our product features",
        context_summary="Product documentation, feature guides, and user manuals",
        attach_context_summary=True,  # Attach full context to prompt
        k=5
    )

    print_result(result, "First Message with Context Summary")
    # Expected: Context included in optimized_prompt


# ========== EXAMPLE 10: Platform-Specific Formatting ==========
def example_platform_specific():
    """Example of platform-specific output formatting"""

    platforms = ["chatGPT", "perplexity", "gemini"]

    for platform in platforms:
        result = call_agentic_rag(
            user_id="user-123",
            profile_id="profile-456",
            query="Explain: print('hello')",
            platform=platform,
            k=3
        )

        print(f"\n🎯 Platform: {platform}")
        print(f"Prompt formatting: {result.get('optimized_prompt')[:100]}...")


# ========== EXAMPLE 11: Comparison Legacy vs Agentic ==========
def example_compare_legacy_vs_agentic():
    """Compare legacy and agentic RAG endpoints"""

    payload = {
        "userId": "user-123",
        "profileId": "profile-456",
        "query": "What is deep learning?",
        "k": 5,
        "chatHistory": [],
        "contextSummary": "",
        "attachContextSummary": False,
        "platform": "chatGPT"
    }

    # Call legacy endpoint
    legacy_url = f"{API_BASE_URL}/rag/rag-query"
    legacy_response = requests.post(
        legacy_url,
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        json=payload
    )
    legacy_result = legacy_response.json()

    # Call agentic endpoint
    agentic_url = f"{API_BASE_URL}/rag/agentic-rag-query"
    agentic_response = requests.post(
        agentic_url,
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
        json=payload
    )
    agentic_result = agentic_response.json()

    print(f"\n{'=' * 80}")
    print("COMPARISON: Legacy vs Agentic RAG")
    print(f"{'=' * 80}")

    print(f"\n📊 Token Usage:")
    print(f"  Legacy:  {legacy_result.get('tokens_used', {}).get('total_tokens', 'N/A')} tokens")
    print(f"  Agentic: {agentic_result.get('tokens_used', {}).get('total_tokens', 'N/A')} tokens")

    print(f"\n📋 Results:")
    print(f"  Legacy:  {legacy_result.get('total_contexts_found', 0)} contexts")
    print(f"  Agentic: {agentic_result.get('total_contexts_found', 0)} contexts")

    print(f"\n✨ Agentic Metadata:")
    metadata = agentic_result.get('workflow_metadata', {})
    print(f"  Query Type: {metadata.get('query_type')}")
    print(f"  Language: {metadata.get('language')}")
    print(f"  Query Expanded: {metadata.get('query_expanded')}")
    print(f"  Context Relevant: {metadata.get('context_relevant')}")

    print(f"\n{'=' * 80}\n")


# ========== RUN ALL EXAMPLES ==========
def run_all_examples():
    """Run all examples"""

    print("\n" + "="*80)
    print("AGENTIC RAG EXAMPLES")
    print("="*80)

    try:
        example_simple_query()
        example_vague_query()
        example_conversational_query()
        example_complex_query()
        example_query_with_data()
        example_no_profile()
        example_multilanguage_query()
        example_romanized_language()
        example_first_message_with_context()
        example_platform_specific()
        example_compare_legacy_vs_agentic()

        print("\n✅ All examples completed successfully!")

    except Exception as e:
        print(f"\n❌ Error running examples: {str(e)}")


if __name__ == "__main__":
    # Configuration
    # Update these if needed
    API_BASE_URL = "http://localhost:8000"

    # Get API key from environment or use default
    import os
    from dotenv import load_dotenv
    load_dotenv()
    API_KEY = os.getenv("CONTEXT_API_KEY", "dev-key-12345")

    print(f"Using API Key: {API_KEY}")
    print(f"Using API URL: {API_BASE_URL}")
    print()

    # Run a specific example
    # example_simple_query()

    # Or run all examples
    run_all_examples()
