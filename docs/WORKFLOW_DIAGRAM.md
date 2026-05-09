# Agentic RAG Workflow Visual Diagrams

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          User Query Input                                │
│                    "tell me about machine learning"                      │
└────────────────────────────┬────────────────────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────────────────┐
│                        Query Analysis                                   │
│  Classifies: simple | vague | conversational | complex                 │
│  Result: "vague" → needs expansion                                      │
└────────────────────────────┬───────────────────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────────────────┐
│                     Chat History Optimization                           │
│  Reduces token usage, preserves recent messages                        │
└────────────────────────────┬───────────────────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────────────────┐
│                   Separate Query & Data                                 │
│  Query: "tell me about machine learning"                               │
│  Data: "None"                                                           │
└────────────────────────────┬───────────────────────────────────────────┘
                             ↓
                    ┌────────┴─────────┐
                    │   Router Node    │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ↓                    ↓                    ↓
┌───────────────┐   ┌────────────────┐   ┌──────────────┐
│ Expand Query  │   │ Direct Retrieve│   │Skip Retrieval│
│ (if vague)    │   │ (if specific)  │   │ (no profile) │
└───────┬───────┘   └────────┬───────┘   └──────┬───────┘
        │                    │                    │
        └────────────┬───────┴────────────────────┘
                     ↓
┌────────────────────────────────────────────────────────────────────────┐
│                      Vector Retrieval                                   │
│  Search embedding DB, apply filters, get top-k results                 │
└────────────────────────────┬───────────────────────────────────────────┘
                             ↓
                    ┌────────┴─────────┐
                    │   Router Node    │
                    └────────┬─────────┘
                             │
                ┌────────────┼────────────┐
                ↓                         ↓
┌───────────────────────┐      ┌────────────────────┐
│  Check Relevance      │      │   Skip Check       │
│  (if docs found)      │      │   (no docs)        │
└───────┬───────────────┘      └────────┬───────────┘
        │                                │
        └────────────┬───────────────────┘
                     ↓
┌────────────────────────────────────────────────────────────────────────┐
│                      Language Detection                                 │
│  Detects: English, Spanish, Roman Urdu, etc.                           │
└────────────────────────────┬───────────────────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────────────────┐
│                   Generate Optimized Prompt                             │
│  Creates final prompt based on query type, context, language           │
└────────────────────────────┬───────────────────────────────────────────┘
                             ↓
┌────────────────────────────────────────────────────────────────────────┐
│                          Response                                       │
│  {                                                                      │
│    "optimized_prompt": "...",                                          │
│    "context": "...",                                                   │
│    "workflow_metadata": {                                              │
│      "query_type": "vague",                                            │
│      "language": "English",                                            │
│      "query_expanded": true                                            │
│    }                                                                   │
│  }                                                                      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Node Flow

### 1. Query Analysis Node

```
Input: "tell me more"
         ↓
┌─────────────────────────┐
│  Analyze with LLM       │
│  - Check specificity    │
│  - Check clarity        │
│  - Check context needs  │
└───────────┬─────────────┘
            ↓
    Classification Result
            ↓
    ┌───────┴───────┐
    │               │
Simple/Complex   Vague
    │               │
    └───────┬───────┘
            ↓
    Set flags:
    needs_query_expansion = True/False
```

### 2. Query Expansion Node (Conditional)

```
Trigger: query_type == "vague" AND contextSummary exists

Input:
  Query: "tell me more"
  Context Summary: "Python ML documentation"
         ↓
┌─────────────────────────┐
│  Expansion Prompt       │
│  - Use context summary  │
│  - Use chat history     │
│  - Infer user intent    │
└───────────┬─────────────┘
            ↓
    Enhanced Query
            ↓
  "Provide more information about Python
   machine learning libraries, frameworks,
   and their usage patterns"
```

### 3. Retrieval Node

```
Input: Enhanced Query OR Original Query
         ↓
┌─────────────────────────┐
│  Generate Embedding     │
│  query_vector = embed() │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│  Apply Filters          │
│  - userId               │
│  - profileId            │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│  Vector Search          │
│  top_k = 5 results      │
└───────────┬─────────────┘
            ↓
    [doc1, doc2, doc3]
            ↓
┌─────────────────────────┐
│  Extract Content        │
│  Sort by chunk order    │
└───────────┬─────────────┘
            ↓
    Combined Context
```

### 4. Relevance Check Node (Conditional)

```
Trigger: relevant_docs is not empty

Input:
  Query: "What is ML?"
  Context: "Python is a programming language..."
         ↓
┌─────────────────────────┐
│  Relevance Prompt       │
│  - Compare query/context│
│  - Check semantic match │
└───────────┬─────────────┘
            ↓
    ┌───────┴────────┐
    │                │
Relevant        Not Relevant
    │                │
Keep Context    Clear Context
    │                │
    └───────┬────────┘
            ↓
    context_is_relevant = True/False
```

### 5. Language Detection Node

```
Input: "Machine learning kya hai?"
         ↓
┌─────────────────────────┐
│  Language Analysis      │
│  - Check script         │
│  - Check vocabulary     │
│  - Check grammar        │
└───────────┬─────────────┘
            ↓
    ┌───────┴────────┐
    │                │
Native Script   Romanized
    │                │
"English"      "Roman Urdu"
"Spanish"      "Roman Arabic"
"Arabic"       "Roman Hindi"
    │                │
    └───────┬────────┘
            ↓
    language = "Roman Urdu"
```

### 6. Prompt Generation Node

```
Inputs:
  - Query: "What is ML?"
  - Context: "Machine learning is..."
  - Language: "English"
  - Query Type: "simple"
         ↓
┌─────────────────────────┐
│  Meta Prompt Builder    │
│  - Set AI role          │
│  - Include context      │
│  - Set language         │
│  - Add data if present  │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│  LLM Generation         │
│  Generate final prompt  │
└───────────┬─────────────┘
            ↓
┌─────────────────────────┐
│  Post-processing        │
│  - Append data          │
│  - Append context       │
│  - Format for platform  │
└───────────┬─────────────┘
            ↓
    Optimized Prompt
```

---

## Routing Decision Trees

### Router 1: After Query Separation

```
                    Query Separated
                          ↓
                   Has profileId?
                          │
            ┌─────────────┴─────────────┐
            NO                          YES
            │                            │
     Skip Retrieval              Is query vague?
            │                            │
            │              ┌─────────────┴─────────────┐
            │             YES                          NO
            │              │                            │
            │       Has contextSummary?          Direct Retrieval
            │              │
            │        ┌─────┴─────┐
            │       YES          NO
            │        │            │
            │   Expand Query  Direct Retrieval
            │        │            │
            └────────┴────────────┴──────────→
                          ↓
                  Continue Workflow
```

### Router 2: After Retrieval

```
                  Contexts Retrieved
                          ↓
                   Any docs found?
                          │
            ┌─────────────┴─────────────┐
            NO                          YES
            │                            │
       Skip Check                Need relevance check?
            │                            │
            │              ┌─────────────┴─────────────┐
            │             YES                          NO
            │              │                            │
            │         Check Relevance              Skip Check
            │              │                            │
            └──────────────┴────────────────────────────┘
                                  ↓
                          Continue Workflow
```

---

## Example Flow Scenarios

### Scenario 1: Simple Query with Context

```
User: "What is Python?"
Profile: "python-dev"

┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Analyze │ → │ History │ → │Separate │ → │Retrieve │
│ simple  │    │ optimize│    │ Q & D   │    │ 3 docs  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                   ↓
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│Generate │ ← │ Detect  │ ← │ Check   │ ← │ Relevant│
│ Prompt  │    │ English │    │Relevant │    │ Context │
└─────────┘    └─────────┘    └─────────┘    └─────────┘

Total: 6 nodes executed
Time: ~1.8s
Tokens: ~1800
```

### Scenario 2: Vague Query with Expansion

```
User: "tell me more"
Profile: "ml-docs"
Context Summary: "Machine learning tutorials"

┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Analyze │ → │ History │ → │Separate │ → │ Expand  │
│  vague  │    │ optimize│    │ Q & D   │    │ Query   │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                   ↓
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│Generate │ ← │ Detect  │ ← │ Check   │ ← │Retrieve │
│ Prompt  │    │ English │    │Relevant │    │ 5 docs  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘

Total: 7 nodes executed (+ expansion)
Time: ~2.3s
Tokens: ~2200
```

### Scenario 3: No Profile (Skip Retrieval)

```
User: "What is AI?"
Profile: "" (empty)

┌─────────┐    ┌─────────┐    ┌─────────┐
│ Analyze │ → │ History │ → │Separate │ → [SKIP RETRIEVAL]
│ simple  │    │ optimize│    │ Q & D   │
└─────────┘    └─────────┘    └─────────┘
                                  ↓
                    ┌─────────┐    ┌─────────┐
                    │ Detect  │ → │Generate │
                    │ English │    │ Prompt  │
                    └─────────┘    └─────────┘

Total: 5 nodes executed (skipped retrieval + relevance)
Time: ~0.5s (75% faster!)
Tokens: ~800
```

---

## State Transitions

```
State Structure:
┌─────────────────────────────────────────────┐
│ AgenticRAGState                             │
├─────────────────────────────────────────────┤
│ Input:                                      │
│  - user_query                               │
│  - user_id, profile_id                      │
│  - chat_history                             │
│  - context_summary                          │
│  - k (top-k contexts)                       │
│                                             │
│ Intermediate:                               │
│  - query_type ← set by analyze_query        │
│  - language ← set by detect_language        │
│  - separated_query ← set by separate_Q_D    │
│  - enhanced_query ← set by expand_query     │
│  - relevant_docs ← set by retrieve          │
│  - context ← set by retrieve/check_rel      │
│                                             │
│ Flags:                                      │
│  - needs_query_expansion ← analyze_query    │
│  - context_is_relevant ← check_relevance    │
│                                             │
│ Output:                                     │
│  - optimized_prompt ← generate_prompt       │
│  - total_tokens_used ← all nodes            │
│  - errors ← any node failures               │
└─────────────────────────────────────────────┘
```

---

## Comparison: Legacy vs Agentic

### Legacy Flow (Sequential)

```
Request → Separate → Language → Retrieve → Relevance → Prompt → Response
  ↓         ↓          ↓          ↓           ↓          ↓
 All      All        All       All         All        All
steps    steps      steps     steps       steps      steps
execute  execute    execute   execute     execute    execute

Problem: No skipping, all steps always execute
```

### Agentic Flow (Conditional)

```
Request → Analyze → Route → [Dynamic Execution] → Response
            ↓         ↓
         Classify  Decide
                     ↓
        ┌────────────┼────────────┐
        ↓            ↓            ↓
    Expand      Retrieve      Skip
     Path        Path         Path
        ↓            ↓            ↓
    [4 nodes]   [3 nodes]   [2 nodes]

Benefit: Only executes necessary steps
```

---

## Token Usage Breakdown

### Simple Query (No Expansion)

```
Node               | Input Tokens | Output Tokens | Total
-------------------|--------------|---------------|-------
Initialize         | 0            | 0             | 0
Analyze Query      | 250          | 20            | 270
Optimize History   | 0            | 0             | 0 (no history)
Separate Q&D       | 300          | 50            | 350
Retrieve           | 0            | 0             | 0 (embedding only)
Check Relevance    | 400          | 50            | 450
Detect Language    | 100          | 10            | 110
Generate Prompt    | 500          | 120           | 620
-------------------|--------------|---------------|-------
TOTAL              | 1550         | 250           | 1800
```

### Vague Query (With Expansion)

```
Node               | Input Tokens | Output Tokens | Total
-------------------|--------------|---------------|-------
Initialize         | 0            | 0             | 0
Analyze Query      | 250          | 20            | 270
Optimize History   | 0            | 0             | 0
Separate Q&D       | 300          | 50            | 350
Expand Vague Query | 450          | 80            | 530 ← EXTRA
Retrieve           | 0            | 0             | 0
Check Relevance    | 400          | 50            | 450
Detect Language    | 100          | 10            | 110
Generate Prompt    | 500          | 120           | 620
-------------------|--------------|---------------|-------
TOTAL              | 2000         | 330           | 2330
```

---

## Error Handling Flow

```
               Any Node Fails
                     ↓
              ┌──────┴──────┐
              │ Try/Except  │
              └──────┬──────┘
                     ↓
         ┌───────────┴───────────┐
         │                       │
     Critical              Non-Critical
         │                       │
  Raise Exception          Add to errors[]
         │                       │
    Stop Workflow          Continue with fallback
                                 ↓
                    ┌────────────┴────────────┐
                    │                         │
              Use default             Log error
                    │                         │
                    └────────────┬────────────┘
                                 ↓
                         Continue Workflow
                                 ↓
                     Include errors in response
```

---

## Monitoring Dashboards

### Key Metrics

```
┌─────────────────────────────────────────────────────────┐
│ Query Type Distribution                                 │
├─────────────────────────────────────────────────────────┤
│ Simple:         ████████████████████████ 45%            │
│ Vague:          ████████████ 25%                        │
│ Conversational: ████████ 18%                            │
│ Complex:        ████ 12%                                │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Average Token Usage by Query Type                       │
├─────────────────────────────────────────────────────────┤
│ Simple:         1,800 tokens ████████████               │
│ Vague:          2,300 tokens ███████████████            │
│ Conversational: 2,100 tokens █████████████              │
│ Complex:        3,200 tokens █████████████████████      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Context Relevance Rate                                  │
├─────────────────────────────────────────────────────────┤
│ Relevant:       ████████████████████████████ 72%        │
│ Not Relevant:   ████████ 28%                            │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Average Latency by Path                                 │
├─────────────────────────────────────────────────────────┤
│ Skip Retrieval:      0.5s █                             │
│ Direct Retrieval:    1.8s ████                          │
│ With Expansion:      2.3s █████                         │
│ Full Path:           2.8s ██████                        │
└─────────────────────────────────────────────────────────┘
```

---

## Conclusion

This visual guide shows how the Agentic RAG system dynamically adapts its execution path based on:
- Query characteristics
- Available data
- Context relevance
- User profile

The result is a more efficient, accurate, and maintainable RAG system.
