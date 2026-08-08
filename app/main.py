from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.api.context_routes import context_router
from app.config.settings import download_nltk_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fetch NLTK data (used by the markdown document loader) at startup rather
    # than import time, so the app still boots offline / in CI. The Docker image
    # pre-downloads these packages; this is a no-op there.
    try:
        download_nltk_data()
    except Exception as e:
        print(f"[WARNING] NLTK data download failed, markdown parsing may degrade: {e}")
    yield


# Initialize FastAPI
app = FastAPI(
    title="Plurality Market AI Service",
    description="Embedding, retrieval, and context-extraction service for marketplace memory buckets: indexes user contexts into a vector store and serves similarity search for the Plurality market stack",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(context_router)

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
    uvicorn.run(app, host="0.0.0.0", port=8001)
