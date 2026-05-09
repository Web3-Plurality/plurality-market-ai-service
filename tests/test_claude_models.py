"""
Test suite specifically for Claude models via Bedrock.
Run with: test_venv\Scripts\python test_claude_models.py
"""
import asyncio
import aiohttp
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# API endpoint configuration
AI_SERVICE_URL = os.getenv("AI_SERVICE_URL", "http://localhost:8000")
AGENTIC_QUERY_ENDPOINT = f"{AI_SERVICE_URL}/rag/agentic-query"
API_KEY = os.getenv("CONTEXT_API_KEY", "dev-key-12345")


@dataclass
class TestResult:
    model_key: str
    model_name: str
    test_name: str
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class ModelTestSuite:
    model_key: str
    model_name: str
    provider: str
    results: List[TestResult] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.success)


# Claude models to test - 6 models (3 removed due to AccessDeniedException)
CLAUDE_MODELS = [
    {"key": "claude-opus-4.5", "name": "Claude Opus 4.5", "provider": "Anthropic"},
    {"key": "claude-opus-4.1", "name": "Claude Opus 4.1", "provider": "Anthropic"},
    # Note: Claude Opus 4 removed - AccessDeniedException on tool calls
    # Note: Claude Sonnet 4.5 removed - AccessDeniedException on tool calls
    {"key": "claude-sonnet-4", "name": "Claude Sonnet 4", "provider": "Anthropic"},
    {"key": "claude-sonnet-3.7", "name": "Claude Sonnet 3.7", "provider": "Anthropic"},
    {"key": "claude-sonnet-3.5", "name": "Claude Sonnet 3.5", "provider": "Anthropic"},
    {"key": "claude-haiku-4.5", "name": "Claude Haiku 4.5", "provider": "Anthropic"},
    # Note: Claude Haiku 3 removed - AccessDeniedException on tool calls
]


class ClaudeModelTester:
    def __init__(self):
        self.results: List[ModelTestSuite] = []
        self.session: Optional[aiohttp.ClientSession] = None

    async def _make_request(self, query: str, model: str, enable_web_search: bool = False,
                           enable_url_extraction: bool = False) -> Dict[str, Any]:
        """Make a request to the agentic-query endpoint"""
        payload = {
            "userId": "test_user",
            "profileId": "test_profile",
            "query": query,
            "chatHistory": [],
            "contextSummary": [],
            "enableWebSearch": enable_web_search,
            "enableUrlExtraction": enable_url_extraction,
            "model": model
        }

        headers = {
            "X-API-Key": API_KEY,
            "Content-Type": "application/json"
        }

        async with self.session.post(
            AGENTIC_QUERY_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=120)
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"HTTP {response.status}: {error_text[:500]}")
            return await response.json()

    async def test_basic_message(self, model_key: str) -> TestResult:
        """Test 1: Send a basic message and get a response"""
        start_time = time.time()
        try:
            result = await self._make_request(
                query="Hello! Please respond with a brief greeting and confirm you are working.",
                model=model_key,
                enable_web_search=False,
                enable_url_extraction=False
            )

            duration = time.time() - start_time
            response = result.get("answer", "") or result.get("response", "")

            if response and len(response) > 10:
                return TestResult(
                    model_key=model_key,
                    model_name="",
                    test_name="Basic Message",
                    success=True,
                    response=f"{response[:150]}...",
                    duration_seconds=duration
                )
            else:
                return TestResult(
                    model_key=model_key,
                    model_name="",
                    test_name="Basic Message",
                    success=False,
                    error=f"Empty or short response: {response[:50]}",
                    duration_seconds=duration
                )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                model_key=model_key,
                model_name="",
                test_name="Basic Message",
                success=False,
                error=str(e)[:200],
                duration_seconds=duration
            )

    async def test_web_search(self, model_key: str) -> TestResult:
        """Test 2: Web search functionality"""
        start_time = time.time()
        try:
            result = await self._make_request(
                query="What is the current weather in New York City today? Please search the web for this information.",
                model=model_key,
                enable_web_search=True,
                enable_url_extraction=False
            )

            duration = time.time() - start_time
            response = result.get("answer", "") or result.get("response", "")
            tool_info = result.get("dynamic_tool_calls", {})
            web_search_performed = tool_info.get("webSearchPerformed", False)
            web_queries = tool_info.get("webSearchQueries", [])

            # Check if web search was invoked or if response mentions weather
            has_weather_info = any(word in response.lower() for word in ["temperature", "weather", "degrees", "forecast", "conditions", "celsius", "fahrenheit", "apologize", "sorry"])

            if response and (web_search_performed or has_weather_info):
                return TestResult(
                    model_key=model_key,
                    model_name="",
                    test_name="Web Search",
                    success=True,
                    response=f"Web search: {web_search_performed}, queries: {web_queries}. Response: {response[:150]}...",
                    duration_seconds=duration
                )
            else:
                return TestResult(
                    model_key=model_key,
                    model_name="",
                    test_name="Web Search",
                    success=False,
                    error=f"Web search not used. Performed: {web_search_performed}. Response: {response[:100]}",
                    duration_seconds=duration
                )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                model_key=model_key,
                model_name="",
                test_name="Web Search",
                success=False,
                error=str(e)[:200],
                duration_seconds=duration
            )

    async def test_url_extraction(self, model_key: str) -> TestResult:
        """Test 3: URL extraction from https://example.com"""
        start_time = time.time()
        try:
            result = await self._make_request(
                query="Please extract and summarize the main content from https://example.com - what is this page about?",
                model=model_key,
                enable_web_search=False,
                enable_url_extraction=True
            )

            duration = time.time() - start_time
            response = result.get("answer", "") or result.get("response", "")
            tool_info = result.get("dynamic_tool_calls", {})
            url_extraction_performed = tool_info.get("urlExtractionPerformed", False)
            extracted_urls = tool_info.get("extractedUrls", [])

            # Check if URL extraction was invoked or if response mentions example.com content
            has_example_info = any(word in response.lower() for word in ["example", "domain", "iana", "placeholder", "documentation", "illustrative"])

            if response and (url_extraction_performed or has_example_info):
                return TestResult(
                    model_key=model_key,
                    model_name="",
                    test_name="URL Extraction",
                    success=True,
                    response=f"URL extraction: {url_extraction_performed}, URLs: {extracted_urls}. Response: {response[:150]}...",
                    duration_seconds=duration
                )
            else:
                return TestResult(
                    model_key=model_key,
                    model_name="",
                    test_name="URL Extraction",
                    success=False,
                    error=f"URL extraction not used. Performed: {url_extraction_performed}. Response: {response[:100]}",
                    duration_seconds=duration
                )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                model_key=model_key,
                model_name="",
                test_name="URL Extraction",
                success=False,
                error=str(e)[:200],
                duration_seconds=duration
            )

    async def run_all_tests(self):
        """Run all tests for all Claude models"""
        print("=" * 80)
        print("CLAUDE MODELS TEST SUITE")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Testing {len(CLAUDE_MODELS)} Claude models")
        print(f"API Endpoint: {AGENTIC_QUERY_ENDPOINT}")
        print("=" * 80)
        print()

        self.session = aiohttp.ClientSession()

        try:
            for model in CLAUDE_MODELS:
                suite = ModelTestSuite(
                    model_key=model["key"],
                    model_name=model["name"],
                    provider=model["provider"]
                )

                print("=" * 60)
                print(f"Testing: {model['name']} ({model['key']})")
                print("=" * 60)

                # Test 1: Basic message
                print("  [1/3] Testing basic message...")
                result1 = await self.test_basic_message(model["key"])
                result1.model_name = model["name"]
                suite.results.append(result1)
                print(f"        {'PASS' if result1.success else 'FAIL'} ({result1.duration_seconds:.2f}s)")
                if not result1.success:
                    print(f"        Error: {result1.error[:80]}...")

                # Add delay between tests to avoid rate limiting
                await asyncio.sleep(2)

                # Test 2: Web search
                print("  [2/3] Testing web search...")
                result2 = await self.test_web_search(model["key"])
                result2.model_name = model["name"]
                suite.results.append(result2)
                print(f"        {'PASS' if result2.success else 'FAIL'} ({result2.duration_seconds:.2f}s)")
                if not result2.success:
                    print(f"        Error: {result2.error[:80]}...")

                # Add delay between tests
                await asyncio.sleep(2)

                # Test 3: URL extraction
                print("  [3/3] Testing URL extraction...")
                result3 = await self.test_url_extraction(model["key"])
                result3.model_name = model["name"]
                suite.results.append(result3)
                print(f"        {'PASS' if result3.success else 'FAIL'} ({result3.duration_seconds:.2f}s)")
                if not result3.success:
                    print(f"        Error: {result3.error[:80]}...")

                print(f"\n  Summary: {suite.passed}/3 passed, {suite.failed}/3 failed")
                self.results.append(suite)
                print()

                # Add delay between models to avoid rate limiting
                await asyncio.sleep(3)

        finally:
            await self.session.close()

    def print_summary(self):
        """Print summary of all test results"""
        total_tests = sum(len(s.results) for s in self.results)
        passed_tests = sum(s.passed for s in self.results)

        print("=" * 80)
        print("TEST RESULTS SUMMARY")
        print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()
        print(f"OVERALL: {passed_tests}/{total_tests} tests passed ({100*passed_tests/total_tests:.1f}%)")
        print(f"Models tested: {len(self.results)}")
        print()

        # Summary table
        print("=" * 80)
        print("SUMMARY TABLE")
        print("=" * 80)
        print()
        print(f"{'Model':<30} {'Basic':<10} {'WebSearch':<12} {'URLExtract':<12}")
        print("-" * 70)

        for suite in self.results:
            basic = next((r for r in suite.results if r.test_name == "Basic Message"), None)
            web = next((r for r in suite.results if r.test_name == "Web Search"), None)
            url = next((r for r in suite.results if r.test_name == "URL Extraction"), None)

            print(f"{suite.model_name:<30} "
                  f"{'PASS' if basic and basic.success else 'FAIL':<10} "
                  f"{'PASS' if web and web.success else 'FAIL':<12} "
                  f"{'PASS' if url and url.success else 'FAIL':<12}")

        # Models with failures
        failed_models = [s for s in self.results if s.failed > 0]
        if failed_models:
            print()
            print("=" * 80)
            print("MODELS WITH FAILURES")
            print("=" * 80)
            for suite in failed_models:
                print(f"\n  {suite.model_name}")
                for result in suite.results:
                    if not result.success:
                        print(f"    - {result.test_name}: {result.error[:70]}...")

        # Fully passing models
        passing_models = [s for s in self.results if s.failed == 0]
        print()
        print("=" * 80)
        print(f"FULLY PASSING MODELS ({len(passing_models)}/{len(self.results)})")
        print("=" * 80)
        for suite in passing_models:
            print(f"  - {suite.model_name}")

        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"claude_test_results_{timestamp}.txt"
        filepath = os.path.join(os.path.dirname(__file__), filename)

        with open(filepath, 'w') as f:
            f.write(f"Claude Models Test Results\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Overall: {passed_tests}/{total_tests} passed\n\n")

            for suite in self.results:
                f.write(f"\n{suite.model_name} ({suite.model_key})\n")
                f.write("-" * 50 + "\n")
                for result in suite.results:
                    status = "PASS" if result.success else "FAIL"
                    f.write(f"  [{status}] {result.test_name} ({result.duration_seconds:.2f}s)\n")
                    if result.error:
                        f.write(f"         Error: {result.error}\n")

        print(f"\nReport saved to: {filepath}")


async def main():
    tester = ClaudeModelTester()
    await tester.run_all_tests()
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
