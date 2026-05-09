"""
Helper functions for tracking metrics in AI Service
"""
import time
import functools
from typing import Callable, Optional, TypeVar, ParamSpec
from app.services.metrics_service import (
    db_query_duration,
    db_query_total,
    vector_operation_duration,
    vector_operation_total,
    llm_call_duration,
    llm_call_total,
    llm_tokens_used,
    llm_input_length,
    llm_output_length,
    embedding_generation_duration,
    embedding_generation_total,
    document_processing_duration,
    document_processing_total,
    document_size,
    document_chunks_created,
    rag_query_duration,
    rag_query_total,
    agentic_workflow_duration,
    agentic_workflow_total,
    web_search_duration,
    web_search_total,
    error_total,
)

P = ParamSpec('P')
T = TypeVar('T')


def measure_db_query(operation: str, table: str):
    """Decorator to measure database query execution time"""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                db_query_duration.labels(operation=operation, table=table, status=status).observe(duration)
                db_query_total.labels(operation=operation, table=table, status=status).inc()

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                db_query_duration.labels(operation=operation, table=table, status=status).observe(duration)
                db_query_total.labels(operation=operation, table=table, status=status).inc()

        # Return async wrapper if function is async, otherwise return sync wrapper
        if functools.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def measure_vector_operation(operation: str):
    """Decorator to measure vector database operations"""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                vector_operation_duration.labels(operation=operation, status=status).observe(duration)
                vector_operation_total.labels(operation=operation, status=status).inc()

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                vector_operation_duration.labels(operation=operation, status=status).observe(duration)
                vector_operation_total.labels(operation=operation, status=status).inc()

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def measure_llm_call(provider: str, model: str, operation: str):
    """Decorator to measure LLM API calls"""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                llm_call_duration.labels(
                    provider=provider, model=model, operation=operation, status=status
                ).observe(duration)
                llm_call_total.labels(
                    provider=provider, model=model, operation=operation, status=status
                ).inc()

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                llm_call_duration.labels(
                    provider=provider, model=model, operation=operation, status=status
                ).observe(duration)
                llm_call_total.labels(
                    provider=provider, model=model, operation=operation, status=status
                ).inc()

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def track_llm_tokens(provider: str, model: str, prompt_tokens: int = 0, completion_tokens: int = 0, total_tokens: int = 0):
    """Track LLM token usage"""
    if prompt_tokens > 0:
        llm_tokens_used.labels(provider=provider, model=model, type="prompt").inc(prompt_tokens)
    if completion_tokens > 0:
        llm_tokens_used.labels(provider=provider, model=model, type="completion").inc(completion_tokens)
    if total_tokens > 0:
        llm_tokens_used.labels(provider=provider, model=model, type="total").inc(total_tokens)


def track_llm_input_output(provider: str, model: str, operation: str, input_length: int, output_length: int):
    """Track LLM input and output lengths"""
    llm_input_length.labels(provider=provider, model=model, operation=operation).observe(input_length)
    llm_output_length.labels(provider=provider, model=model, operation=operation).observe(output_length)


def measure_embedding_generation(model: str):
    """Decorator to measure embedding generation"""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                embedding_generation_duration.labels(model=model, status=status).observe(duration)
                embedding_generation_total.labels(model=model, status=status).inc()

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                embedding_generation_duration.labels(model=model, status=status).observe(duration)
                embedding_generation_total.labels(model=model, status=status).inc()

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def measure_document_processing(file_type: str):
    """Decorator to measure document processing"""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                document_processing_duration.labels(file_type=file_type, status=status).observe(duration)
                document_processing_total.labels(file_type=file_type, status=status).inc()

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                document_processing_duration.labels(file_type=file_type, status=status).observe(duration)
                document_processing_total.labels(file_type=file_type, status=status).inc()

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def track_document_metrics(file_type: str, size_bytes: int, chunks_count: int):
    """Track document size and chunks created"""
    document_size.labels(file_type=file_type).observe(size_bytes)
    document_chunks_created.labels(file_type=file_type).observe(chunks_count)


def measure_rag_query(query_type: str):
    """Decorator to measure RAG query processing"""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                rag_query_duration.labels(query_type=query_type, status=status).observe(duration)
                rag_query_total.labels(query_type=query_type, status=status).inc()

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                rag_query_duration.labels(query_type=query_type, status=status).observe(duration)
                rag_query_total.labels(query_type=query_type, status=status).inc()

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def measure_agentic_workflow(workflow_type: str):
    """Decorator to measure agentic workflow execution"""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                agentic_workflow_duration.labels(workflow_type=workflow_type, status=status).observe(duration)
                agentic_workflow_total.labels(workflow_type=workflow_type, status=status).inc()

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                agentic_workflow_duration.labels(workflow_type=workflow_type, status=status).observe(duration)
                agentic_workflow_total.labels(workflow_type=workflow_type, status=status).inc()

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def measure_web_search():
    """Decorator to measure web search operations"""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                web_search_duration.labels(status=status).observe(duration)
                web_search_total.labels(status=status).inc()

        @functools.wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            start_time = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise e
            finally:
                duration = time.time() - start_time
                web_search_duration.labels(status=status).observe(duration)
                web_search_total.labels(status=status).inc()

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def track_error(service: str, error_type: str, severity: str = "medium"):
    """Track errors"""
    error_total.labels(service=service, error_type=error_type, severity=severity).inc()
