from fastapi import FastAPI, Response
from app.api.context_routes import context_router
from app.middleware.metrics_middleware import PrometheusMiddleware
from app.services.metrics_service import get_metrics

# Initialize FastAPI
app = FastAPI(
    title="Plurality AI Context Service",
    description="A comprehensive RAG (Retrieval-Augmented Generation) service for managing and querying personal knowledge bases",
    version="1.0.0"
)

# Add Prometheus middleware
app.add_middleware(PrometheusMiddleware)

# Include routers
app.include_router(context_router)

# Metrics endpoint for Prometheus
@app.get("/metrics")
async def metrics():
    """Expose Prometheus metrics"""
    return Response(content=get_metrics(), media_type="text/plain")

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "context-service",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
