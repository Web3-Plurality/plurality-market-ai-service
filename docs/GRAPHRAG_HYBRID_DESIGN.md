# GraphRAG Hybrid Architecture Design
## Plurality AI Service - Architectural Overview

**Document Version:** 1.0
**Created:** 2025-11-17
**Status:** Architecture Specification
**Target:** Hybrid Vector + GraphRAG System

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Design Principles](#design-principles)
3. [System Architecture](#system-architecture)
4. [Component Architecture](#component-architecture)
5. [Data Flow Architecture](#data-flow-architecture)
6. [Integration Architecture](#integration-architecture)
7. [Strategy Decision Architecture](#strategy-decision-architecture)
8. [Storage Architecture](#storage-architecture)

---

## Architecture Overview

### What We're Building

A **hybrid retrieval system** that intelligently combines vector search (semantic similarity) with GraphRAG (relationship reasoning) through agent-driven strategy selection.

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    API LAYER                                │
│             FastAPI Endpoints                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              ORCHESTRATION LAYER                            │
│         Agentic RAG Service (LangGraph)                     │
│  • Strategy Classification                                  │
│  • Workflow Coordination                                    │
│  • State Management                                         │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│  RETRIEVAL LAYER │    │  RETRIEVAL LAYER │
│  Vector Service  │    │  GraphRAG Service│
│  • Embeddings    │    │  • Entity Extract│
│  • Similarity    │    │  • Graph Traverse│
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│  STORAGE LAYER   │    │  STORAGE LAYER   │
│  S3 Vectors DB   │    │  NetworkX/Neo4j  │
└──────────────────┘    └──────────────────┘
```

### Key Architectural Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Strategy Selection** | Agent-driven (LLM) | Adapts to query nuances, no brittle rules |
| **Execution Model** | Parallel async | Max performance for hybrid queries |
| **Graph Storage** | NetworkX (MVP) → Neo4j (scale) | Fast iteration, clear migration path |
| **Integration Pattern** | Non-disruptive enhancement | Zero risk to existing functionality |
| **Failure Handling** | Graceful degradation | Always return result, prefer partial over none |

---

## Design Principles

### 1. Intelligence at the Orchestration Layer

**Principle:** Let the agent decide the retrieval strategy dynamically.

```
┌────────────────────────────────────────────────────────┐
│  Query: "What is the relationship between X and Y?"    │
└────────────────────┬───────────────────────────────────┘
                     │
                     ▼
            ┌────────────────────┐
            │  LLM Classifier     │
            │  Analyzes:          │
            │  • Query intent     │
            │  • Complexity       │
            │  • Keywords         │
            └────────┬───────────┘
                     │
                     ▼
            "graph_local" strategy selected
                     │
                     ▼
            ┌────────────────────┐
            │  Graph Traversal   │
            │  Returns:          │
            │  • Entity paths    │
            │  • Relationships   │
            └────────────────────┘
```

**Benefits:**
- Adapts to new query patterns without code changes
- No maintenance of complex rule sets
- Leverages LLM understanding of nuance

### 2. Parallel Execution

**Principle:** When both retrieval methods add value, run them concurrently.

```
Traditional Sequential (5.0s):
├─ Query Graph (3.2s)
└─ Query Vector (1.8s)
Total: 5.0s

Parallel Architecture (3.2s):
├─ Query Graph (3.2s)  ┐
└─ Query Vector (1.8s) ├─ await asyncio.gather()
Total: max(3.2s, 1.8s) = 3.2s
```

**Impact:** 36% latency reduction

### 3. Separation of Concerns

**Principle:** Each layer has a single, well-defined responsibility.

```
API Layer:           Request/Response handling
Orchestration:       Workflow & strategy decisions
Retrieval:           Execute search operations
Storage:             Persist & query data
```

### 4. Graceful Degradation

**Principle:** System never fails completely due to partial failure.

```
Hybrid Query Execution:
├─ Try: Vector + Graph (parallel)
│  ├─ Vector Success + Graph Fail → Use vector only
│  ├─ Vector Fail + Graph Success → Use graph only
│  └─ Both Fail → Empty context, workflow continues
└─ Result: Always returns response
```

---

## System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  Browser/App → POST /rag/agentic-rag-query                                  │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            API LAYER (FastAPI)                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  context_routes.py                                                   │   │
│  │  • POST /rag/agentic-rag-query  (main endpoint)                     │   │
│  │  • POST /graph/query            (direct graph query)                │   │
│  │  • GET  /graph/stats            (graph statistics)                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SERVICE LAYER (Business Logic)                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  context_service.py (Wrapper)                                        │   │
│  │  • Validates requests                                                │   │
│  │  • Formats responses                                                 │   │
│  └────────────────────────┬─────────────────────────────────────────────┘   │
│                           │                                                  │
│                           ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  agentic_rag_service.py (Orchestrator - LangGraph)                  │   │
│  │                                                                       │   │
│  │  State Machine Workflow:                                             │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │  [Initialize]                                                 │   │   │
│  │  │       ↓                                                        │   │   │
│  │  │  [Analyze Query] → Classify: simple/vague/complex            │   │   │
│  │  │       ↓                                                        │   │   │
│  │  │  [Classify Strategy] → Decide: vector/graph/hybrid           │   │   │
│  │  │       ↓                                                        │   │   │
│  │  │  [Optimize Chat History]                                      │   │   │
│  │  │       ↓                                                        │   │   │
│  │  │  [Separate Query/Data]                                        │   │   │
│  │  │       ↓                                                        │   │   │
│  │  │  [Conditional: Expand Vague Query]                            │   │   │
│  │  │       ↓                                                        │   │   │
│  │  │  [Retrieve Contexts] ← STRATEGY ROUTER                        │   │   │
│  │  │       ├─────────┬─────────┬─────────┐                        │   │   │
│  │  │       ▼         ▼         ▼         ▼                         │   │   │
│  │  │    vector  graph_local  graph_global hybrid                   │   │   │
│  │  │       │         │         │         │                         │   │   │
│  │  │       └─────────┴─────────┴─────────┘                        │   │   │
│  │  │       ↓                                                        │   │   │
│  │  │  [Check Relevance]                                            │   │   │
│  │  │       ↓                                                        │   │   │
│  │  │  [Detect Language]                                            │   │   │
│  │  │       ↓                                                        │   │   │
│  │  │  [Generate Prompt]                                            │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────┬───────────────────────────┘
                       │                          │
                       ▼                          ▼
┌────────────────────────────────────┐  ┌──────────────────────────────────┐
│   RETRIEVAL LAYER                  │  │   RETRIEVAL LAYER                │
│   vector_service.py                │  │   graph_rag_service.py           │
│                                    │  │                                  │
│   • _embed_text()                  │  │   • index_document()             │
│   • query_vectors()                │  │   • query_graph_local()          │
│   • similarity_search()            │  │   • query_graph_global()         │
│                                    │  │   • _extract_entities()          │
│                                    │  │   • _detect_communities()        │
└────────────┬───────────────────────┘  └──────────┬───────────────────────┘
             │                                     │
             ▼                                     ▼
┌────────────────────────────────────┐  ┌──────────────────────────────────┐
│   STORAGE LAYER                    │  │   STORAGE LAYER                  │
│   S3 Vectors / Pinecone            │  │   NetworkX (in-memory)           │
│                                    │  │   OR Neo4j (persistent)          │
│   • Vector embeddings              │  │                                  │
│   • Metadata filters               │  │   • Knowledge graph              │
│   • Similarity index               │  │   • Entity/relationship storage  │
└────────────────────────────────────┘  └──────────────────────────────────┘
```

### Service Dependencies

```
┌──────────────────────┐
│   BaseService        │
│   • LLM clients      │
│   • BGE embeddings   │
│   • S3 Vectors       │
│   • Tools            │
└─────────┬────────────┘
          │ (inherits)
          │
    ┌─────┴──────────────────────┐
    │                            │
    ▼                            ▼
┌──────────────┐        ┌──────────────────┐
│VectorService │        │GraphRAGService   │
└──────┬───────┘        └────────┬─────────┘
       │                         │
       └────────┬────────────────┘
                │
                ▼
       ┌──────────────────┐
       │AgenticRAGService │
       │  (uses both)     │
       └──────────────────┘
```

---

## Component Architecture

### Component 1: Agentic RAG Service (Orchestrator)

**Responsibility:** Workflow coordination and strategy routing

```
┌─────────────────────────────────────────────────────────────┐
│            AgenticRAGService                                │
│                                                             │
│  State: AgenticRAGState (TypedDict)                        │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Input Fields:                                      │   │
│  │  • user_query, user_id, profile_id                 │   │
│  │  • chat_history, context_summary                   │   │
│  │  • k (retrieval count)                             │   │
│  │                                                      │   │
│  │  Processing Fields:                                 │   │
│  │  • query_type (simple/vague/conversational/complex)│   │
│  │  • retrieval_strategy (vector/graph_*/hybrid)      │   │
│  │  • is_multi_hop_query                              │   │
│  │  • separated_query, enhanced_query                 │   │
│  │                                                      │   │
│  │  Output Fields:                                     │   │
│  │  • context, sources, optimized_prompt              │   │
│  │  • workflow_metadata, tokens_used                  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  Key Methods:                                              │
│  • process_rag_query() → Entry point                      │
│  • _classify_retrieval_strategy_node() → NEW              │
│  • _retrieve_contexts_node() → MODIFIED (router)          │
│  • _retrieve_vector_contexts() → Extracted               │
│  • _retrieve_graph_contexts() → NEW                       │
│  • _retrieve_hybrid_contexts() → NEW                      │
└─────────────────────────────────────────────────────────────┘
```

### Component 2: GraphRAG Service

**Responsibility:** Knowledge graph operations

```
┌─────────────────────────────────────────────────────────────┐
│            GraphRAGService                                  │
│                                                             │
│  Graph Storage:                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │  self.graphs: Dict[user_id, Dict[profile_id, G]]   │   │
│  │                                                      │   │
│  │  Structure per graph (NetworkX MultiDiGraph):      │   │
│  │  • Nodes: Entities with attributes                 │   │
│  │    - name, type, description                       │   │
│  │    - mention_count, source_docs                    │   │
│  │  • Edges: Relationships                            │   │
│  │    - relationship type                             │   │
│  │    - description, confidence                       │   │
│  │    - source_doc                                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  Indexing Pipeline:                                        │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Document → LLM Extraction → Entities + Relations  │   │
│  │  → Add to Graph → Update Communities Cache         │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  Query Modes:                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Local Search (k-hop traversal):                   │   │
│  │  Query → Find entities → Expand k-hops → Subgraph │   │
│  │                                                      │   │
│  │  Global Search (community summaries):              │   │
│  │  Query → Detect communities → Summarize each →    │   │
│  │  → Aggregate summaries                             │   │
│  └────────────────────────────────────────────────────┘   │
│                                                             │
│  Key Methods:                                              │
│  • index_document()                                        │
│  • query_graph_local(k_hops=2)                            │
│  • query_graph_global()                                    │
│  • _extract_entities_relationships() → LLM call           │
│  • _find_relevant_entities() → Semantic search            │
│  • _detect_communities() → Louvain algorithm              │
└─────────────────────────────────────────────────────────────┘
```

### Component 3: Vector Service

**Responsibility:** Semantic search operations

```
┌─────────────────────────────────────────────────────────────┐
│            VectorService                                    │
│                                                             │
│  Embedding Model:                                          │
│  • BGE (BAAI/bge-large-en-v1.5)                           │
│  • 1024 dimensions                                         │
│  • Cosine similarity                                       │
│                                                             │
│  Storage:                                                  │
│  • S3 Vectors (AWS managed)                               │
│  • Metadata filtering (userId, profileId)                 │
│  • Top-k retrieval                                         │
│                                                             │
│  Key Methods:                                              │
│  • query_vectors(embedding, top_k, filters)               │
│  • store_vectors(vectors_data)                            │
│  • _embed_text(text) → vector[1024]                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow Architecture

### Flow 1: Vector-Only Query

```
User Request
    ↓
POST /rag/agentic-rag-query
{
  "query": "What is machine learning?",
  "userId": "user-123",
  "profileId": "profile-456"
}
    ↓
┌─────────────────────────────────────────┐
│  Initialize State                       │
│  • user_query = "What is ML?"          │
│  • user_id, profile_id                 │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Analyze Query (LLM)                    │
│  • Classification: "simple"             │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Classify Strategy                      │
│  • No multi-hop keywords                │
│  • query_type = "simple"                │
│  • Decision: strategy = "vector"        │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Retrieve Contexts (Vector)             │
│  ┌──────────────────────────────────┐  │
│  │ 1. Embed query → [0.23, -0.15...]│  │
│  │ 2. S3 Vectors search (top_k=5)   │  │
│  │ 3. Retrieve 5 documents          │  │
│  │ 4. Assemble context text         │  │
│  └──────────────────────────────────┘  │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Check Relevance (LLM)                  │
│  • context_is_relevant = true           │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Generate Prompt (LLM)                  │
│  • optimized_prompt created             │
└────────────┬────────────────────────────┘
             │
             ▼
Response: {
  "optimized_prompt": "...",
  "context": "ML is...",
  "sources": [...],
  "workflow_metadata": {
    "retrieval_strategy": "vector",
    "query_type": "simple",
    "tokens_used": 1800
  }
}
```

### Flow 2: Multi-Hop Query (Graph)

```
User Request
    ↓
POST /rag/agentic-rag-query
{
  "query": "What is the relationship between Django and Python?",
  "userId": "user-123",
  "profileId": "profile-456"
}
    ↓
┌─────────────────────────────────────────┐
│  Initialize State                       │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Analyze Query (LLM)                    │
│  • Classification: "simple"             │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Classify Strategy                      │
│  • Multi-hop keyword: "relationship"    │
│  • query_type = "simple"                │
│  • Decision: strategy = "graph_local"   │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Retrieve Contexts (Graph Local)        │
│  ┌──────────────────────────────────┐  │
│  │ 1. Embed query                   │  │
│  │ 2. Find entities: [django, python│  │
│  │ 3. Expand 2-hops                 │  │
│  │    django → python (written_in)  │  │
│  │    python → guido (created_by)   │  │
│  │ 4. Extract subgraph (12 nodes)   │  │
│  │ 5. Convert to text context       │  │
│  └──────────────────────────────────┘  │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Check Relevance                        │
│  • context_is_relevant = true           │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Generate Prompt                        │
└────────────┬────────────────────────────┘
             │
             ▼
Response: {
  "context": "=== Entities ===\nDjango...",
  "workflow_metadata": {
    "retrieval_strategy": "graph_local",
    "graph_metadata": {
      "entry_entities": ["django", "python"],
      "subgraph_nodes": 12,
      "subgraph_edges": 15
    }
  }
}
```

### Flow 3: Hybrid Query (Parallel)

```
User Request
    ↓
POST /rag/agentic-rag-query
{
  "query": "Explain Django ORM with code examples",
  "userId": "user-123",
  "profileId": "profile-456"
}
    ↓
┌─────────────────────────────────────────┐
│  Analyze Query → "complex"              │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Classify Strategy → "hybrid"           │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Retrieve Contexts (Hybrid)             │
│                                         │
│  ┌─────────────────┐ ┌──────────────┐ │
│  │ ASYNC TASK 1    │ │ ASYNC TASK 2 │ │
│  │ Vector Search   │ │ Graph Search │ │
│  │ ↓               │ │ ↓            │ │
│  │ Code examples   │ │ Relationships│ │
│  │ 5 docs          │ │ 8 nodes      │ │
│  │ 1.8s            │ │ 2.1s         │ │
│  └────────┬────────┘ └──────┬───────┘ │
│           │                  │         │
│           └────────┬─────────┘         │
│                    ▼                   │
│         await asyncio.gather()         │
│                    ↓                   │
│           Merge Contexts:              │
│           ┌────────────────────┐       │
│           │ === Vector ===     │       │
│           │ Code examples...   │       │
│           │                    │       │
│           │ === Graph ===      │       │
│           │ Relationships...   │       │
│           └────────────────────┘       │
│                                         │
│  Total time: max(1.8s, 2.1s) = 2.1s   │
└─────────────────────────────────────────┘
    ↓
Response: {
  "context": "=== Vector ===\n... === Graph ===\n...",
  "sources": [vector_sources + graph_sources],
  "workflow_metadata": {
    "retrieval_strategy": "hybrid",
    "vector_latency_ms": 1842,
    "graph_latency_ms": 2156
  }
}
```

---

## Integration Architecture

### Non-Disruptive Integration Pattern

```
┌─────────────────────────────────────────────────────────────┐
│  BEFORE: Existing Agentic RAG                               │
│                                                             │
│  [Initialize] → [Analyze] → [Optimize] → [Separate] →     │
│  → [Expand] → [Retrieve (Vector Only)] → [Relevance] →    │
│  → [Language] → [Generate]                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  AFTER: Hybrid Enhancement                                  │
│                                                             │
│  [Initialize] → [Analyze] → [Classify Strategy] ← NEW      │
│  → [Optimize] → [Separate] → [Expand] →                   │
│  → [Retrieve (Router)] ← MODIFIED                          │
│      ├─ vector (existing)                                  │
│      ├─ graph_local (new)                                  │
│      ├─ graph_global (new)                                 │
│      └─ hybrid (new)                                       │
│  → [Relevance] → [Language] → [Generate]                  │
└─────────────────────────────────────────────────────────────┘
```

**Changes Required:**

1. **Add State Fields:**
```python
class AgenticRAGState(TypedDict):
    # Existing fields (unchanged)
    user_query: str
    user_id: str
    # ...

    # NEW fields
    is_multi_hop_query: bool
    use_graph_retrieval: bool
    retrieval_strategy: str  # "vector" | "graph_local" | "graph_global" | "hybrid"
    graph_metadata: dict
```

2. **Add New Node:**
```python
.add_node("classify_strategy", self._classify_retrieval_strategy_node)
.add_edge("analyze_query", "classify_strategy")
.add_edge("classify_strategy", "optimize_chat_history")
```

3. **Modify Retrieval Node:**
```python
async def _retrieve_contexts_node(state):
    strategy = state["retrieval_strategy"]

    if strategy == "vector":
        return await _retrieve_vector_contexts(state)
    elif strategy == "graph_local":
        return await _retrieve_graph_contexts(state, mode="local")
    elif strategy == "hybrid":
        return await _retrieve_hybrid_contexts(state)
    # ...
```

### Backward Compatibility

```
┌─────────────────────────────────────────┐
│  Feature Flag Control                   │
│                                         │
│  if not settings.ENABLE_GRAPH_RAG:     │
│      strategy = "vector"  # Always     │
│                                         │
│  Ensures:                              │
│  • Can disable GraphRAG instantly      │
│  • A/B testing support                 │
│  • Gradual rollout capability          │
└─────────────────────────────────────────┘
```

---

## Strategy Decision Architecture

### Decision Tree

```
Query Received
    │
    ▼
┌─────────────────────────────────────────────────┐
│  Step 1: Extract Features                       │
│  • query_text                                   │
│  • query_type (from analyze_query)              │
│  • context_summary                              │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│  Step 2: Check Multi-Hop Keywords               │
│  Keywords: [                                    │
│    "relationship between",                      │
│    "connection between",                        │
│    "how are X and Y related",                   │
│    "founded by", "created by",                  │
│    "built with", "used by",                     │
│    "compare", "difference between"              │
│  ]                                              │
└────────────┬────────────────────────────────────┘
             │
             ▼
        Multi-hop detected?
             │
    ┌────────┴────────┐
    │ YES             │ NO
    │                 │
    ▼                 ▼
query_type?      query_type?
    │                 │
    │            ┌────┴────┐
    │            │ complex │ other
    │            │         │
    │            ▼         ▼
    │        "hybrid"  "vector"
    │
    ┌────┴────┐
    │simple/  │complex
    │convers  │
    │         │
    ▼         ▼
"graph_    "hybrid"
 local"
```

### Strategy Selection Matrix

| Query Type | Multi-Hop? | Strategy | Rationale |
|------------|-----------|----------|-----------|
| simple | Yes | `graph_local` | Fast graph traversal for clear relationship query |
| simple | No | `vector` | Standard semantic search |
| conversational | Yes | `graph_local` | Relationship context needed |
| conversational | No | `vector` | Follow-up question, use history |
| vague | Yes | `hybrid` | Need both expansion and relationships |
| vague | No | `vector` | Query expansion → vector search |
| complex | Yes | `hybrid` | Multi-part with relationships → comprehensive |
| complex | No | `hybrid` | Multi-part → needs both code + concepts |

**Special Cases:**
- "summarize all" or "overview" → `graph_global`
- No `profile_id` → `skip_retrieval`

---

## Storage Architecture

### Dual Storage Model

```
┌─────────────────────────────────────────────────────────────┐
│                    VECTOR STORAGE                           │
│                                                             │
│  S3 Vectors / Pinecone                                     │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Document Chunks:                                   │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │ ID: "chunk-123"                              │  │   │
│  │  │ Vector: [0.23, -0.15, 0.08, ..., 0.42]      │  │   │
│  │  │         (1024 dimensions)                     │  │   │
│  │  │ Metadata: {                                  │  │   │
│  │  │   userId: "user-123",                        │  │   │
│  │  │   profileId: "profile-456",                  │  │   │
│  │  │   content: "Full text...",                   │  │   │
│  │  │   fileName: "doc.pdf",                       │  │   │
│  │  │   contentType: "file"                        │  │   │
│  │  │ }                                            │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  │                                                      │   │
│  │  Optimized for:                                     │   │
│  │  • Cosine similarity search                         │   │
│  │  • Top-k retrieval                                  │   │
│  │  • Metadata filtering                               │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    GRAPH STORAGE                            │
│                                                             │
│  NetworkX (MVP) / Neo4j (Production)                       │
│  ┌────────────────────────────────────────────────────┐   │
│  │  Knowledge Graph per user/profile:                 │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │  Nodes (Entities):                           │  │   │
│  │  │  {                                            │  │   │
│  │  │    "python": {                                │  │   │
│  │  │      name: "Python",                          │  │   │
│  │  │      type: "ProgrammingLanguage",             │  │   │
│  │  │      description: "High-level language...",   │  │   │
│  │  │      mention_count: 15,                       │  │   │
│  │  │      source_docs: ["doc1", "doc2", ...]       │  │   │
│  │  │    },                                         │  │   │
│  │  │    "django": { ... }                          │  │   │
│  │  │  }                                            │  │   │
│  │  │                                               │  │   │
│  │  │  Edges (Relationships):                       │  │   │
│  │  │  [                                            │  │   │
│  │  │    ("django", "python", {                     │  │   │
│  │  │      relationship: "written_in",              │  │   │
│  │  │      description: "Django is built in Python",│  │   │
│  │  │      source_doc: "doc1",                      │  │   │
│  │  │      weight: 0.95                             │  │   │
│  │  │    })                                         │  │   │
│  │  │  ]                                            │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  │                                                      │   │
│  │  Optimized for:                                     │   │
│  │  • k-hop traversal                                  │   │
│  │  • Relationship queries                             │   │
│  │  • Community detection                              │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Storage Isolation

```
User/Profile Isolation:

Vector DB:
  Filter: { userId: "user-123", profileId: "profile-456" }
  → Returns only user's documents

Graph DB:
  Structure: self.graphs["user-123"]["profile-456"]
  → Separate graph per user/profile
  → No cross-user data leakage
```

### Data Consistency

```
Document Upload Flow:

1. Document Received
    ↓
2. [PARALLEL]
   ├─ Vector Indexing
   │  • Chunk document
   │  • Generate embeddings
   │  • Store in vector DB
   │
   └─ Graph Indexing (async background)
      • Extract entities/relationships
      • Update knowledge graph
      • Invalidate community cache

3. User sees vector results immediately
   Graph results available after indexing completes
```

---

## Summary

### Architectural Highlights

✅ **Layered Architecture**
- Clear separation: API → Orchestration → Retrieval → Storage
- Each layer has single responsibility
- Easy to test and maintain

✅ **Agent-Driven Intelligence**
- LLM-based strategy selection
- No brittle rule systems
- Adapts to query nuances

✅ **Parallel Execution**
- Hybrid queries run vector + graph simultaneously
- 36% latency reduction
- Graceful degradation on failure

✅ **Non-Disruptive Integration**
- Existing vector RAG unchanged
- GraphRAG added as enhancement
- Feature flags for safe rollout

✅ **Dual Storage Model**
- Vector DB: Semantic similarity
- Graph DB: Relationship reasoning
- User/profile isolation

### Key Architectural Patterns

1. **Strategy Pattern:** Multiple retrieval strategies selected at runtime
2. **Orchestrator Pattern:** Central coordinator (LangGraph) manages workflow
3. **Parallel Execution Pattern:** Async/await for concurrent operations
4. **Graceful Degradation Pattern:** Fallback on component failure
5. **Repository Pattern:** Separate storage concerns from business logic

---

**End of Architecture Document**

For implementation details, see:
- [agentic_rag_service.py](app/services/agentic_rag_service.py)
- [AGENTIC_RAG_GUIDE.md](docs/AGENTIC_RAG_GUIDE.md)
