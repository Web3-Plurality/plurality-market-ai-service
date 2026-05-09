"""
Prometheus metrics middleware for FastAPI
"""
import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.services.metrics_service import (
    http_request_duration,
    http_request_total,
    http_active_requests,
    http_request_size,
    http_response_size,
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP metrics for Prometheus"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # Skip metrics collection for the /metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        endpoint = request.url.path

        # Normalize endpoint to remove IDs and dynamic segments
        endpoint = self._normalize_endpoint(endpoint)

        # Track active requests
        http_active_requests.labels(method=method, endpoint=endpoint).inc()

        # Track request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                request_size = int(content_length)
                http_request_size.labels(method=method, endpoint=endpoint).observe(request_size)
            except ValueError:
                pass

        # Measure request duration
        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code

            # Track response size if available
            if hasattr(response, "headers") and "content-length" in response.headers:
                try:
                    response_size = int(response.headers["content-length"])
                    http_response_size.labels(method=method, endpoint=endpoint).observe(response_size)
                except (ValueError, KeyError):
                    pass

            return response

        except Exception as e:
            # Track errors with 500 status code
            status_code = 500
            raise e

        finally:
            # Calculate duration
            duration = time.time() - start_time

            # Record metrics
            http_request_duration.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).observe(duration)

            http_request_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()

            # Decrement active requests
            http_active_requests.labels(method=method, endpoint=endpoint).dec()

    @staticmethod
    def _normalize_endpoint(path: str) -> str:
        """
        Normalize endpoint paths to group similar routes together.
        Replace dynamic segments like UUIDs with placeholders.
        """
        parts = path.split("/")
        normalized_parts = []

        for part in parts:
            # Skip empty parts
            if not part:
                continue

            # Replace UUIDs and numeric IDs with placeholders
            if _is_uuid(part):
                normalized_parts.append("{uuid}")
            elif part.isdigit():
                normalized_parts.append("{id}")
            else:
                normalized_parts.append(part)

        return "/" + "/".join(normalized_parts) if normalized_parts else "/"


def _is_uuid(value: str) -> bool:
    """Check if a string is a UUID"""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False
