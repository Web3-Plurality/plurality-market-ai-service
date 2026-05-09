# Agentic RAG Setup & Testing Guide

## Installation

### 1. Install Dependencies

```bash
# Install langgraph
pip install langgraph==0.2.59

# Or install all requirements
pip install -r requirements.txt
```

### 2. Verify Installation

```python
# Test import
python -c "from langgraph.graph import StateGraph; print('LangGraph installed successfully!')"
```

---

## Quick Start

### 1. Start the Service

```bash
# From the project root
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Test the Endpoint

```bash
curl -X POST "http://localhost:8000/rag/agentic-rag-query" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "test-user",
    "profileId": "test-profile",
    "query": "What is machine learning?",
    "k": 5,
    "chatHistory": [],
    "contextSummary": "",
    "attachContextSummary": false,
    "platform": "chatGPT"
  }'
```

### 3. Verify Response

Expected response structure:
```json
{
  "query": "What is machine learning?",
  "optimized_prompt": "...",
  "context": "...",
  "sources": [...],
  "total_contexts_found": 3,
  "workflow_metadata": {
    "query_type": "simple",
    "language": "English",
    "query_expanded": false,
    "context_relevant": true,
    "separated_query": "What is machine learning?",
    "separated_data": "None",
    "errors": []
  }
}
```

---

## Testing Scenarios

### Test 1: Simple Query (No Context)

```python
import requests

response = requests.post(
    "http://localhost:8000/rag/agentic-rag-query",
    headers={"X-API-Key": "your-api-key"},
    json={
        "userId": "test-user",
        "profileId": "",  # No profile = skip retrieval
        "query": "What is Python?",
        "k": 5
    }
)

result = response.json()
print(f"Query Type: {result['workflow_metadata']['query_type']}")
print(f"Contexts Found: {result['total_contexts_found']}")
# Expected: query_type="simple", total_contexts_found=0
```

### Test 2: Vague Query Expansion

```python
response = requests.post(
    "http://localhost:8000/rag/agentic-rag-query",
    headers={"X-API-Key": "your-api-key"},
    json={
        "userId": "test-user",
        "profileId": "test-profile",
        "query": "tell me more",
        "contextSummary": "Machine learning documentation",
        "k": 5
    }
)

result = response.json()
print(f"Query Expanded: {result['workflow_metadata']['query_expanded']}")
# Expected: query_expanded=True
```

### Test 3: Context Relevance Check

```python
response = requests.post(
    "http://localhost:8000/rag/agentic-rag-query",
    headers={"X-API-Key": "your-api-key"},
    json={
        "userId": "test-user",
        "profileId": "test-profile",
        "query": "What is machine learning?",
        "k": 5
    }
)

result = response.json()
print(f"Context Relevant: {result['workflow_metadata']['context_relevant']}")
print(f"Context Length: {len(result['context'])}")
# Expected: context_relevant=True (if relevant docs found)
```

### Test 4: Language Detection

```python
# English query
response = requests.post(
    "http://localhost:8000/rag/agentic-rag-query",
    headers={"X-API-Key": "your-api-key"},
    json={
        "userId": "test-user",
        "profileId": "test-profile",
        "query": "What is AI?",
        "k": 5
    }
)
print(f"Language: {response.json()['workflow_metadata']['language']}")
# Expected: language="English"

# Spanish query
response = requests.post(
    "http://localhost:8000/rag/agentic-rag-query",
    headers={"X-API-Key": "your-api-key"},
    json={
        "userId": "test-user",
        "profileId": "test-profile",
        "query": "¿Qué es la inteligencia artificial?",
        "k": 5
    }
)
print(f"Language: {response.json()['workflow_metadata']['language']}")
# Expected: language="Spanish"
```

### Test 5: Conversational Query

```python
response = requests.post(
    "http://localhost:8000/rag/agentic-rag-query",
    headers={"X-API-Key": "your-api-key"},
    json={
        "userId": "test-user",
        "profileId": "test-profile",
        "query": "What about the other one?",
        "chatHistory": [
            {"role": "user", "content": "Tell me about supervised learning"},
            {"role": "assistant", "content": "Supervised learning is..."}
        ],
        "k": 5
    }
)

result = response.json()
print(f"Query Type: {result['workflow_metadata']['query_type']}")
# Expected: query_type="conversational"
```

---

## Performance Testing

### Load Test with Apache Bench

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Create test payload
cat > test_payload.json << EOF
{
  "userId": "test-user",
  "profileId": "test-profile",
  "query": "What is machine learning?",
  "k": 5,
  "chatHistory": [],
  "contextSummary": "",
  "attachContextSummary": false,
  "platform": "chatGPT"
}
EOF

# Run load test (100 requests, 10 concurrent)
ab -n 100 -c 10 -p test_payload.json -T application/json \
  -H "X-API-Key: your-api-key" \
  http://localhost:8000/rag/agentic-rag-query
```

### Token Usage Analysis

```python
import requests
import statistics

def test_token_usage(num_runs=10):
    """Test average token usage"""

    token_counts = []

    for _ in range(num_runs):
        response = requests.post(
            "http://localhost:8000/rag/agentic-rag-query",
            headers={"X-API-Key": "your-api-key"},
            json={
                "userId": "test-user",
                "profileId": "test-profile",
                "query": "What is deep learning?",
                "k": 5
            }
        )

        result = response.json()
        tokens = result['tokens_used']['total_tokens']
        token_counts.append(tokens)

    print(f"Average Tokens: {statistics.mean(token_counts):.2f}")
    print(f"Min Tokens: {min(token_counts)}")
    print(f"Max Tokens: {max(token_counts)}")
    print(f"Std Dev: {statistics.stdev(token_counts):.2f}")

test_token_usage()
```

### Latency Measurement

```python
import requests
import time
import statistics

def test_latency(num_runs=10):
    """Test average latency"""

    latencies = []

    for _ in range(num_runs):
        start = time.time()

        response = requests.post(
            "http://localhost:8000/rag/agentic-rag-query",
            headers={"X-API-Key": "your-api-key"},
            json={
                "userId": "test-user",
                "profileId": "test-profile",
                "query": "What is machine learning?",
                "k": 5
            }
        )

        latency = time.time() - start
        latencies.append(latency)

    print(f"Average Latency: {statistics.mean(latencies):.2f}s")
    print(f"Min Latency: {min(latencies):.2f}s")
    print(f"Max Latency: {max(latencies):.2f}s")
    print(f"Std Dev: {statistics.stdev(latencies):.2f}s")

test_latency()
```

---

## Debugging

### Enable Debug Logging

Check the console output for detailed workflow logs:

```bash
# Run with verbose output
uvicorn app.main:app --reload --log-level debug
```

### Check Workflow Execution

```python
response = requests.post(
    "http://localhost:8000/rag/agentic-rag-query",
    headers={"X-API-Key": "your-api-key"},
    json={
        "userId": "test-user",
        "profileId": "test-profile",
        "query": "What is AI?",
        "k": 5
    }
)

result = response.json()
metadata = result['workflow_metadata']

print("Workflow Execution:")
print(f"  1. Query Type: {metadata['query_type']}")
print(f"  2. Language: {metadata['language']}")
print(f"  3. Query Expanded: {metadata['query_expanded']}")
print(f"  4. Separated Query: {metadata['separated_query']}")
print(f"  5. Separated Data: {metadata['separated_data']}")
print(f"  6. Context Relevant: {metadata['context_relevant']}")
print(f"  7. Contexts Found: {result['total_contexts_found']}")
print(f"  8. Errors: {metadata['errors']}")
```

### Visualize Workflow (Optional)

```python
from app.services.agentic_rag_service import AgenticRAGService
from langgraph.graph import StateGraph

# Create service
service = AgenticRAGService()

# Get the compiled graph
graph = service.graph

# Print graph structure
print("Graph Nodes:")
for node in graph.nodes:
    print(f"  - {node}")

print("\nGraph Edges:")
for edge in graph.edges:
    print(f"  - {edge}")
```

---

## Common Issues

### Issue 1: ImportError for langgraph

**Error:**
```
ModuleNotFoundError: No module named 'langgraph'
```

**Fix:**
```bash
pip install langgraph==0.2.59
```

### Issue 2: TypeError in StateGraph

**Error:**
```
TypeError: 'type' object is not subscriptable
```

**Fix:**
Ensure you're using Python 3.9+ or import from `typing_extensions`:
```python
from typing_extensions import TypedDict
```

### Issue 3: High Token Usage

**Cause:** All workflow nodes executing even when unnecessary

**Fix:** Check routing logic:
```python
# Verify conditional routing works
result = call_agentic_rag(profile_id="")  # Should skip retrieval
assert result['total_contexts_found'] == 0
```

### Issue 4: Context Not Relevant

**Cause:** Relevance check too strict or context genuinely irrelevant

**Fix:** Adjust relevance prompt or increase k value:
```python
result = call_agentic_rag(k=10)  # Get more contexts
```

---

## Integration Testing

### Test with Existing Data

```python
# First, add some test context
add_context_response = requests.post(
    "http://localhost:8000/rag/add-context",
    headers={"X-API-Key": "your-api-key"},
    json={
        "userId": "test-user",
        "profileId": "test-profile",
        "context": "Python is a high-level programming language known for its simplicity and readability."
    }
)

# Wait for processing
import time
time.sleep(2)

# Now query with agentic RAG
query_response = requests.post(
    "http://localhost:8000/rag/agentic-rag-query",
    headers={"X-API-Key": "your-api-key"},
    json={
        "userId": "test-user",
        "profileId": "test-profile",
        "query": "What is Python?",
        "k": 5
    }
)

result = query_response.json()
print(f"Contexts Found: {result['total_contexts_found']}")
print(f"Context Relevant: {result['workflow_metadata']['context_relevant']}")
# Expected: total_contexts_found > 0, context_relevant=True
```

---

## Monitoring

### Key Metrics to Track

1. **Token Usage per Query**
   - Average: ~2000-3000 tokens
   - Alert if: > 5000 tokens

2. **Latency**
   - Average: ~2-3 seconds
   - Alert if: > 5 seconds

3. **Query Type Distribution**
   - Simple: 40-50%
   - Vague: 20-30%
   - Conversational: 15-25%
   - Complex: 5-15%

4. **Context Relevance Rate**
   - Target: > 70% relevant
   - Alert if: < 50% relevant

5. **Error Rate**
   - Target: < 5%
   - Alert if: > 10%

### Sample Monitoring Script

```python
import requests
import time
from collections import Counter

def monitor_agentic_rag(duration_minutes=5):
    """Monitor agentic RAG performance"""

    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)

    metrics = {
        "total_requests": 0,
        "total_tokens": 0,
        "query_types": Counter(),
        "relevant_contexts": 0,
        "total_contexts": 0,
        "errors": 0
    }

    test_queries = [
        "What is AI?",
        "tell me more",
        "What about the other option?",
        "Compare machine learning and deep learning"
    ]

    while time.time() < end_time:
        query = test_queries[metrics["total_requests"] % len(test_queries)]

        try:
            response = requests.post(
                "http://localhost:8000/rag/agentic-rag-query",
                headers={"X-API-Key": "your-api-key"},
                json={
                    "userId": "test-user",
                    "profileId": "test-profile",
                    "query": query,
                    "k": 5
                },
                timeout=10
            )

            result = response.json()
            metadata = result['workflow_metadata']

            metrics["total_requests"] += 1
            metrics["total_tokens"] += result['tokens_used']['total_tokens']
            metrics["query_types"][metadata['query_type']] += 1

            if metadata['context_relevant']:
                metrics["relevant_contexts"] += 1
            metrics["total_contexts"] += 1

            if metadata['errors']:
                metrics["errors"] += 1

        except Exception as e:
            metrics["errors"] += 1
            print(f"Error: {e}")

        time.sleep(10)  # Wait 10 seconds between requests

    # Print summary
    print("\n=== Monitoring Summary ===")
    print(f"Total Requests: {metrics['total_requests']}")
    print(f"Average Tokens: {metrics['total_tokens'] / metrics['total_requests']:.2f}")
    print(f"Query Types: {dict(metrics['query_types'])}")
    print(f"Relevance Rate: {metrics['relevant_contexts'] / metrics['total_contexts'] * 100:.2f}%")
    print(f"Error Rate: {metrics['errors'] / metrics['total_requests'] * 100:.2f}%")

monitor_agentic_rag(duration_minutes=5)
```

---

## Next Steps

1. ✅ Install dependencies
2. ✅ Start the service
3. ✅ Run basic tests
4. ✅ Test different query types
5. ✅ Measure performance
6. ✅ Monitor in production

For more information, see [AGENTIC_RAG_GUIDE.md](AGENTIC_RAG_GUIDE.md)
