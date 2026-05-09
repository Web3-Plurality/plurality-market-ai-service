"""
Test token tracking across different model families
"""
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
BASE_URL = "http://localhost:8000"
API_KEY = os.getenv("CONTEXT_API_KEY", "dev-key-12345")

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Test models from different families
TEST_MODELS = [
    {"key": "claude-haiku-4.5", "name": "Claude Haiku 4.5", "family": "Claude"},
    {"key": "llama-3.1-8b", "name": "Llama 3.1 8B", "family": "Llama"},
    {"key": "mistral-small", "name": "Mistral Small", "family": "Mistral"},
    {"key": "nova-micro", "name": "Nova Micro", "family": "Nova"},
    {"key": "gpt-oss-120b", "name": "GPT-OSS 120B", "family": "OpenAI"},
]

def test_model_tokens(model_key: str, model_name: str, family: str):
    """Test a single model and check token tracking"""
    print(f"\n{'='*80}")
    print(f"Testing {model_name} ({family} family)")
    print(f"{'='*80}")

    payload = {
        "userId": "test_user",
        "profileId": "test_profile",
        "query": "What is the capital of France?",
        "chatHistory": [],
        "contextSummary": [],
        "enableWebSearch": False,
        "enableUrlExtraction": False,
        "model": model_key
    }

    try:
        response = requests.post(
            f"{BASE_URL}/rag/agentic-query",
            headers=HEADERS,
            json=payload,
            timeout=120
        )

        if response.status_code == 200:
            result = response.json()
            tokens = result.get("tokens_used", {})

            input_tokens = tokens.get("input_tokens", 0)
            output_tokens = tokens.get("output_tokens", 0)
            total_tokens = tokens.get("total_tokens", 0)

            print(f"[OK] {model_name} Response:")
            print(f"  Input:  {input_tokens:4d} tokens")
            print(f"  Output: {output_tokens:4d} tokens")
            print(f"  Total:  {total_tokens:4d} tokens")

            if total_tokens == 0:
                print(f"  [WARNING] No token usage tracked!")
                return False
            else:
                print(f"  [OK] Token tracking WORKING")
                return True
        else:
            print(f"[ERROR] HTTP {response.status_code}")
            print(f"  {response.text}")
            return False

    except Exception as e:
        print(f"[ERROR] Exception: {str(e)}")
        return False

def main():
    print("Token Tracking Test for All Model Families")
    print("=" * 80)

    results = {}

    for model in TEST_MODELS:
        success = test_model_tokens(model["key"], model["name"], model["family"])
        family = model["family"]
        if family not in results:
            results[family] = {"working": 0, "failed": 0}

        if success:
            results[family]["working"] += 1
        else:
            results[family]["failed"] += 1

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY BY MODEL FAMILY")
    print(f"{'='*80}")

    for family, counts in results.items():
        total = counts["working"] + counts["failed"]
        status = "[OK] WORKING" if counts["failed"] == 0 else f"[PARTIAL] ({counts['working']}/{total})"
        print(f"{family:15s}: {status}")

    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
