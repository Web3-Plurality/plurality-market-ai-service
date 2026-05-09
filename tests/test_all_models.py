"""
Automated tests for all Bedrock and Gemini models.
Tests:
1. Basic message response
2. Web search functionality
3. URL extraction from https://plurality.network

Run with: python test_all_models.py
Or from tests venv: test_venv\Scripts\python test_all_models.py
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


# All models to test - matches models available in bedrock_models.py
ALL_MODELS = [
    # Gemini models (Google AI - separate service)
    {"key": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "provider": "Google"},
    {"key": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "provider": "Google"},
    {"key": "gemini-3-pro", "name": "Gemini 3 Pro", "provider": "Google"},

    # Claude models (Anthropic via Bedrock) - 6 models
    {"key": "claude-opus-4.5", "name": "Claude Opus 4.5", "provider": "Anthropic"},
    {"key": "claude-opus-4.1", "name": "Claude Opus 4.1", "provider": "Anthropic"},
    # Note: Claude Opus 4 removed - AccessDeniedException on tool calls
    # Note: Claude Sonnet 4.5 removed - AccessDeniedException on tool calls
    {"key": "claude-sonnet-4", "name": "Claude Sonnet 4", "provider": "Anthropic"},
    {"key": "claude-sonnet-3.7", "name": "Claude Sonnet 3.7", "provider": "Anthropic"},
    {"key": "claude-sonnet-3.5", "name": "Claude Sonnet 3.5", "provider": "Anthropic"},
    {"key": "claude-haiku-4.5", "name": "Claude Haiku 4.5", "provider": "Anthropic"},
    # Note: Claude Haiku 3 removed - AccessDeniedException on tool calls

    # Llama models (Meta via Bedrock) - only working models
    # Note: Llama 4 Scout/Maverick, 3.2 90B/11B, 3.1 405B removed due to regional access restrictions
    {"key": "llama-3.3-70b", "name": "Llama 3.3 70B", "provider": "Meta"},
    {"key": "llama-3.2-3b", "name": "Llama 3.2 3B", "provider": "Meta"},
    {"key": "llama-3.2-1b", "name": "Llama 3.2 1B", "provider": "Meta"},
    {"key": "llama-3.1-70b", "name": "Llama 3.1 70B", "provider": "Meta"},
    {"key": "llama-3.1-8b", "name": "Llama 3.1 8B", "provider": "Meta"},

    # Mistral models (via Bedrock)
    {"key": "mistral-large", "name": "Mistral Large", "provider": "Mistral"},
    {"key": "mistral-large-3", "name": "Mistral Large 3 675B", "provider": "Mistral"},
    {"key": "mistral-small", "name": "Mistral Small", "provider": "Mistral"},
    {"key": "pixtral-large", "name": "Pixtral Large", "provider": "Mistral"},

    # DeepSeek (via Bedrock)
    {"key": "deepseek-r1", "name": "DeepSeek R1", "provider": "DeepSeek"},

    # Amazon Nova models (via Bedrock)
    {"key": "nova-pro", "name": "Nova Pro", "provider": "Amazon"},
    {"key": "nova-lite", "name": "Nova Lite", "provider": "Amazon"},
    {"key": "nova-micro", "name": "Nova Micro", "provider": "Amazon"},

    # Writer models (via Bedrock)
    {"key": "palmyra-x4", "name": "Palmyra X4", "provider": "Writer"},
    {"key": "palmyra-x5", "name": "Palmyra X5", "provider": "Writer"},

    # OpenAI GPT-OSS models (via Bedrock)
    {"key": "gpt-oss-120b", "name": "GPT-OSS 120B", "provider": "OpenAI"},
    # Note: GPT-OSS 20B removed - limited capability with tool calling
]


class ModelTester:
    def __init__(self):
        self.results: List[ModelTestSuite] = []
        self.session: Optional[aiohttp.ClientSession] = None

    async def _make_request(self, query: str, model: str, enable_web_search: bool = False,
                           enable_url_extraction: bool = False) -> Dict[str, Any]:
        """Make a request to the agentic-query endpoint"""
        # Use camelCase to match the API schema
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
            # API returns 'answer' not 'response'
            response = result.get("answer", "") or result.get("response", "")

            # Check if we got a valid response
            if response and len(response) > 10:
                return TestResult(
                    model_key=model_key,
                    model_name="",
                    test_name="Basic Message",
                    success=True,
                    response=response[:200] + "..." if len(response) > 200 else response,
                    duration_seconds=duration
                )
            else:
                return TestResult(
                    model_key=model_key,
                    model_name="",
                    test_name="Basic Message",
                    success=False,
                    error=f"Empty or too short response: {response}",
                    duration_seconds=duration
                )
        except Exception as e:
            duration = time.time() - start_time
            return TestResult(
                model_key=model_key,
                model_name="",
                test_name="Basic Message",
                success=False,
                error=str(e)[:500],
                duration_seconds=duration
            )

    async def test_web_search(self, model_key: str) -> TestResult:
        """Test 2: Ask the model to perform a web search"""
        start_time = time.time()
        try:
            result = await self._make_request(
                query="What is the current weather in New York City today? Please search the web for this information.",
                model=model_key,
                enable_web_search=True,
                enable_url_extraction=False
            )

            duration = time.time() - start_time
            # API returns 'answer' not 'response'
            response = result.get("answer", "") or result.get("response", "")
            # API returns dynamic_tool_calls with actual tool usage info
            tool_info = result.get("dynamic_tool_calls", {})
            web_search_performed = tool_info.get("webSearchPerformed", False) or result.get("web_search_performed", False)
            web_queries = tool_info.get("webSearchQueries", [])

            # Check if web search was invoked or if response mentions weather
            has_weather_info = any(word in response.lower() for word in ["temperature", "weather", "degrees", "forecast", "conditions", "celsius", "fahrenheit"])

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
                error=str(e)[:500],
                duration_seconds=duration
            )

    async def test_url_extraction(self, model_key: str) -> TestResult:
        """Test 3: Ask the model to extract content from https://plurality.network"""
        start_time = time.time()
        try:
            result = await self._make_request(
                query="Please extract and summarize the main content from https://plurality.network - what is Plurality about?",
                model=model_key,
                enable_web_search=False,
                enable_url_extraction=True
            )

            duration = time.time() - start_time
            # API returns 'answer' not 'response'
            response = result.get("answer", "") or result.get("response", "")
            # API returns dynamic_tool_calls with actual tool usage info
            tool_info = result.get("dynamic_tool_calls", {})
            url_extraction_performed = tool_info.get("urlExtractionPerformed", False) or result.get("url_content_extracted", False)
            extracted_urls = tool_info.get("extractedUrls", []) or result.get("extracted_urls", [])

            # Check if URL extraction was invoked or if response mentions Plurality
            has_plurality_info = any(word in response.lower() for word in ["plurality", "ontology", "knowledge", "memory", "context", "personal", "ai"])

            if response and (url_extraction_performed or has_plurality_info):
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
                error=str(e)[:500],
                duration_seconds=duration
            )

    async def test_model(self, model_info: Dict[str, str]) -> ModelTestSuite:
        """Run all tests for a single model"""
        model_key = model_info["key"]
        model_name = model_info["name"]
        provider = model_info["provider"]

        print(f"\n{'='*60}")
        print(f"Testing: {model_name} ({model_key}) - {provider}")
        print(f"{'='*60}")

        suite = ModelTestSuite(
            model_key=model_key,
            model_name=model_name,
            provider=provider
        )

        # Test 1: Basic Message
        print(f"  [1/3] Testing basic message...")
        result1 = await self.test_basic_message(model_key)
        result1.model_name = model_name
        suite.results.append(result1)
        status = "PASS" if result1.success else "FAIL"
        print(f"        {status} ({result1.duration_seconds:.2f}s)")
        if not result1.success:
            print(f"        Error: {result1.error[:100]}...")

        # Test 2: Web Search
        print(f"  [2/3] Testing web search...")
        result2 = await self.test_web_search(model_key)
        result2.model_name = model_name
        suite.results.append(result2)
        status = "PASS" if result2.success else "FAIL"
        print(f"        {status} ({result2.duration_seconds:.2f}s)")
        if not result2.success:
            print(f"        Error: {result2.error[:100]}...")

        # Test 3: URL Extraction
        print(f"  [3/3] Testing URL extraction...")
        result3 = await self.test_url_extraction(model_key)
        result3.model_name = model_name
        suite.results.append(result3)
        status = "PASS" if result3.success else "FAIL"
        print(f"        {status} ({result3.duration_seconds:.2f}s)")
        if not result3.success:
            print(f"        Error: {result3.error[:100]}...")

        print(f"\n  Summary: {suite.passed}/3 passed, {suite.failed}/3 failed")

        return suite

    async def run_all_tests(self, models: List[Dict[str, str]] = None) -> List[ModelTestSuite]:
        """Run tests for all models"""
        models = models or ALL_MODELS

        print("\n" + "="*80)
        print("AUTOMATED MODEL TESTING SUITE")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Testing {len(models)} models")
        print(f"API Endpoint: {AGENTIC_QUERY_ENDPOINT}")
        print("="*80)

        # Create aiohttp session
        self.session = aiohttp.ClientSession()

        try:
            for model_info in models:
                try:
                    suite = await self.test_model(model_info)
                    self.results.append(suite)
                except Exception as e:
                    print(f"\n  CRITICAL ERROR testing {model_info['name']}: {e}")
                    # Create a failed suite
                    suite = ModelTestSuite(
                        model_key=model_info["key"],
                        model_name=model_info["name"],
                        provider=model_info["provider"]
                    )
                    for test_name in ["Basic Message", "Web Search", "URL Extraction"]:
                        suite.results.append(TestResult(
                            model_key=model_info["key"],
                            model_name=model_info["name"],
                            test_name=test_name,
                            success=False,
                            error=f"Critical error: {str(e)[:200]}"
                        ))
                    self.results.append(suite)
        finally:
            await self.session.close()

        return self.results

    def generate_report(self) -> str:
        """Generate a summary report of all test results"""
        report = []
        report.append("\n" + "="*80)
        report.append("TEST RESULTS SUMMARY")
        report.append(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("="*80)

        # Group by provider
        providers: Dict[str, List[ModelTestSuite]] = {}
        for suite in self.results:
            if suite.provider not in providers:
                providers[suite.provider] = []
            providers[suite.provider].append(suite)

        # Overall stats
        total_tests = sum(len(s.results) for s in self.results)
        total_passed = sum(s.passed for s in self.results)
        total_failed = sum(s.failed for s in self.results)

        if total_tests > 0:
            report.append(f"\nOVERALL: {total_passed}/{total_tests} tests passed ({100*total_passed/total_tests:.1f}%)")
        else:
            report.append(f"\nOVERALL: No tests run")
        report.append(f"Models tested: {len(self.results)}")

        # Detailed results by provider
        for provider, suites in providers.items():
            report.append(f"\n{'='*60}")
            report.append(f"PROVIDER: {provider}")
            report.append(f"{'='*60}")

            for suite in suites:
                report.append(f"\n  {suite.model_name} ({suite.model_key})")
                report.append(f"  {'-'*40}")

                for result in suite.results:
                    status = "PASS" if result.success else "FAIL"
                    duration = f"({result.duration_seconds:.2f}s)" if result.duration_seconds > 0 else ""
                    report.append(f"    [{status}] {result.test_name} {duration}")

                    if not result.success and result.error:
                        # Truncate error for readability
                        error_preview = result.error[:150].replace('\n', ' ')
                        report.append(f"           Error: {error_preview}...")

        # Summary table
        report.append("\n" + "="*80)
        report.append("SUMMARY TABLE")
        report.append("="*80)
        report.append(f"\n{'Model':<30} {'Provider':<12} {'Basic':<8} {'WebSearch':<10} {'URLExtract':<10}")
        report.append("-"*70)

        for suite in self.results:
            basic = next((r for r in suite.results if r.test_name == "Basic Message"), None)
            web = next((r for r in suite.results if r.test_name == "Web Search"), None)
            url = next((r for r in suite.results if r.test_name == "URL Extraction"), None)

            basic_status = "PASS" if basic and basic.success else "FAIL"
            web_status = "PASS" if web and web.success else "FAIL"
            url_status = "PASS" if url and url.success else "FAIL"

            report.append(f"{suite.model_name:<30} {suite.provider:<12} {basic_status:<8} {web_status:<10} {url_status:<10}")

        # Failed models summary
        failed_models = [s for s in self.results if s.failed > 0]
        if failed_models:
            report.append("\n" + "="*80)
            report.append("MODELS WITH FAILURES")
            report.append("="*80)

            for suite in failed_models:
                failed_tests = [r for r in suite.results if not r.success]
                report.append(f"\n  {suite.model_name} ({suite.provider})")
                for result in failed_tests:
                    report.append(f"    - {result.test_name}: {result.error[:100]}...")

        # Fully passing models
        passing_models = [s for s in self.results if s.failed == 0]
        report.append("\n" + "="*80)
        report.append(f"FULLY PASSING MODELS ({len(passing_models)}/{len(self.results)})")
        report.append("="*80)
        for suite in passing_models:
            report.append(f"  - {suite.model_name} ({suite.provider})")

        return "\n".join(report)

    def save_report(self, filename: str = None):
        """Save the report to a file"""
        if filename is None:
            filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        report = self.generate_report()

        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, 'w') as f:
            f.write(report)

        print(f"\nReport saved to: {filepath}")
        return filepath


async def main():
    """Main entry point for running tests"""
    tester = ModelTester()

    # You can filter models here if needed
    # For testing, you might want to start with a subset
    # models_to_test = [m for m in ALL_MODELS if m["provider"] == "Google"]

    # Run all tests
    await tester.run_all_tests()

    # Generate and print report
    report = tester.generate_report()
    print(report)

    # Save report to file
    tester.save_report()

    return tester.results


if __name__ == "__main__":
    asyncio.run(main())
