"""
Prometheus metrics configuration for AI Service
"""
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, REGISTRY
from typing import Optional

# ===== Service Info =====
service_info = Info('plurality_ai_service', 'AI Service information')
service_info.info({'version': '1.0.0', 'service': 'rag-ai'})

# ===== HTTP Metrics =====
http_request_duration = Histogram(
    'plurality_ai_http_request_duration_seconds',
    'Duration of HTTP requests in seconds',
    ['method', 'endpoint', 'status_code'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10, 30]
)

http_request_total = Counter(
    'plurality_ai_http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_active_requests = Gauge(
    'plurality_ai_http_active_requests',
    'Number of active HTTP requests',
    ['method', 'endpoint']
)

http_request_size = Histogram(
    'plurality_ai_http_request_size_bytes',
    'Size of HTTP requests in bytes',
    ['method', 'endpoint'],
    buckets=[100, 1000, 10000, 100000, 1000000, 10000000]
)

http_response_size = Histogram(
    'plurality_ai_http_response_size_bytes',
    'Size of HTTP responses in bytes',
    ['method', 'endpoint'],
    buckets=[100, 1000, 10000, 100000, 1000000, 10000000]
)

# ===== Database Metrics =====
db_query_duration = Histogram(
    'plurality_ai_db_query_duration_seconds',
    'Duration of database queries in seconds',
    ['operation', 'table', 'status'],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1, 2, 5]
)

db_query_total = Counter(
    'plurality_ai_db_queries_total',
    'Total number of database queries',
    ['operation', 'table', 'status']
)

db_connection_pool_size = Gauge(
    'plurality_ai_db_connection_pool_size',
    'Current database connection pool size'
)

db_connection_pool_active = Gauge(
    'plurality_ai_db_connection_pool_active',
    'Number of active database connections'
)

# ===== Vector Database Metrics =====
vector_operation_duration = Histogram(
    'plurality_ai_vector_operation_duration_seconds',
    'Duration of vector database operations',
    ['operation', 'status'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10, 30]
)

vector_operation_total = Counter(
    'plurality_ai_vector_operations_total',
    'Total number of vector database operations',
    ['operation', 'status']
)

vector_search_results = Histogram(
    'plurality_ai_vector_search_results',
    'Number of results returned from vector searches',
    ['operation'],
    buckets=[1, 5, 10, 20, 50, 100, 200]
)

vector_chunks_stored = Counter(
    'plurality_ai_vector_chunks_stored_total',
    'Total number of vector chunks stored',
    ['user_id']
)

# ===== LLM/AI Metrics =====
llm_call_duration = Histogram(
    'plurality_ai_llm_call_duration_seconds',
    'Duration of LLM API calls',
    ['provider', 'model', 'operation', 'status'],
    buckets=[0.5, 1, 2, 5, 10, 30, 60, 120]
)

llm_call_total = Counter(
    'plurality_ai_llm_calls_total',
    'Total number of LLM API calls',
    ['provider', 'model', 'operation', 'status']
)

llm_tokens_used = Counter(
    'plurality_ai_llm_tokens_total',
    'Total number of LLM tokens used',
    ['provider', 'model', 'type']
)

llm_input_length = Histogram(
    'plurality_ai_llm_input_length_chars',
    'Length of LLM input in characters',
    ['provider', 'model', 'operation'],
    buckets=[100, 500, 1000, 5000, 10000, 50000, 100000]
)

llm_output_length = Histogram(
    'plurality_ai_llm_output_length_chars',
    'Length of LLM output in characters',
    ['provider', 'model', 'operation'],
    buckets=[100, 500, 1000, 5000, 10000, 50000]
)

# ===== Embedding Metrics =====
embedding_generation_duration = Histogram(
    'plurality_ai_embedding_generation_duration_seconds',
    'Duration of embedding generation',
    ['model', 'status'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10]
)

embedding_generation_total = Counter(
    'plurality_ai_embedding_generations_total',
    'Total number of embeddings generated',
    ['model', 'status']
)

embedding_dimension = Gauge(
    'plurality_ai_embedding_dimension',
    'Dimension of embeddings',
    ['model']
)

# ===== Document Processing Metrics =====
document_processing_duration = Histogram(
    'plurality_ai_document_processing_duration_seconds',
    'Duration of document processing',
    ['file_type', 'status'],
    buckets=[0.1, 0.5, 1, 5, 10, 30, 60, 120]
)

document_processing_total = Counter(
    'plurality_ai_document_processing_total',
    'Total number of documents processed',
    ['file_type', 'status']
)

document_size = Histogram(
    'plurality_ai_document_size_bytes',
    'Size of processed documents',
    ['file_type'],
    buckets=[1024, 10240, 102400, 1024000, 10240000, 102400000]
)

document_chunks_created = Histogram(
    'plurality_ai_document_chunks_created',
    'Number of chunks created from documents',
    ['file_type'],
    buckets=[1, 5, 10, 50, 100, 500, 1000]
)

# ===== RAG Query Metrics =====
rag_query_duration = Histogram(
    'plurality_ai_rag_query_duration_seconds',
    'Duration of RAG query processing',
    ['query_type', 'status'],
    buckets=[0.5, 1, 2, 5, 10, 30, 60]
)

rag_query_total = Counter(
    'plurality_ai_rag_queries_total',
    'Total number of RAG queries',
    ['query_type', 'status']
)

rag_context_chunks_retrieved = Histogram(
    'plurality_ai_rag_context_chunks_retrieved',
    'Number of context chunks retrieved for RAG',
    ['query_type'],
    buckets=[1, 3, 5, 10, 20, 50]
)

rag_chat_history_length = Histogram(
    'plurality_ai_rag_chat_history_length',
    'Length of chat history in messages',
    ['query_type'],
    buckets=[1, 5, 10, 20, 50, 100]
)

# ===== Agentic RAG Metrics =====
agentic_workflow_duration = Histogram(
    'plurality_ai_agentic_workflow_duration_seconds',
    'Duration of agentic workflow execution',
    ['workflow_type', 'status'],
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

agentic_workflow_total = Counter(
    'plurality_ai_agentic_workflows_total',
    'Total number of agentic workflows executed',
    ['workflow_type', 'status']
)

agentic_workflow_steps = Histogram(
    'plurality_ai_agentic_workflow_steps',
    'Number of steps in agentic workflow',
    ['workflow_type'],
    buckets=[1, 2, 3, 5, 10, 20]
)

agentic_tool_calls = Counter(
    'plurality_ai_agentic_tool_calls_total',
    'Total number of tool calls in agentic workflows',
    ['tool_name', 'status']
)

# ===== Query Classification Metrics =====
query_classification_total = Counter(
    'plurality_ai_query_classifications_total',
    'Total number of query classifications',
    ['query_type', 'language']
)

query_expansion_total = Counter(
    'plurality_ai_query_expansions_total',
    'Total number of query expansions',
    ['status']
)

# ===== Web Search Metrics =====
web_search_duration = Histogram(
    'plurality_ai_web_search_duration_seconds',
    'Duration of web search operations',
    ['status'],
    buckets=[0.5, 1, 2, 5, 10, 30]
)

web_search_total = Counter(
    'plurality_ai_web_search_total',
    'Total number of web searches',
    ['status']
)

web_search_results = Histogram(
    'plurality_ai_web_search_results',
    'Number of web search results',
    buckets=[1, 5, 10, 20, 50]
)

# ===== Context Management Metrics =====
context_created_total = Counter(
    'plurality_ai_contexts_created_total',
    'Total number of contexts created',
    ['user_id', 'source_type']
)

context_deleted_total = Counter(
    'plurality_ai_contexts_deleted_total',
    'Total number of contexts deleted',
    ['user_id']
)

context_active = Gauge(
    'plurality_ai_contexts_active',
    'Number of active contexts',
    ['user_id']
)

# ===== Error Metrics =====
error_total = Counter(
    'plurality_ai_errors_total',
    'Total number of errors',
    ['service', 'error_type', 'severity']
)

unhandled_errors = Counter(
    'plurality_ai_unhandled_errors_total',
    'Total number of unhandled errors',
    ['type']
)

# ===== Health Metrics =====
health_status = Gauge(
    'plurality_ai_health_status',
    'Health status of the service (1 = healthy, 0 = unhealthy)',
    ['component']
)

# ===== Prompt Metrics =====
prompt_generation_duration = Histogram(
    'plurality_ai_prompt_generation_duration_seconds',
    'Duration of prompt generation',
    ['prompt_type', 'status'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5]
)

prompt_generation_total = Counter(
    'plurality_ai_prompt_generations_total',
    'Total number of prompts generated',
    ['prompt_type', 'status']
)


def get_metrics():
    """Get current metrics in Prometheus format"""
    return generate_latest(REGISTRY)
