import psycopg2
import boto3
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from fastapi import HTTPException
from typing import List
from app.config.settings import settings


class BaseService:
    def __init__(self):
        # Initialize AWS S3 Vectors client
        self.s3vectors_client = boto3.client(
            's3vectors',
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )

        # S3 Vectors configuration
        self.vector_bucket_name = settings.S3_VECTOR_BUCKET_NAME
        self.vector_index_name = settings.S3_VECTOR_INDEX_NAME

        # Initialize HuggingFace BGE embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-large-en-v1.5",
            model_kwargs={'device': 'cpu'},  # Use 'cuda' if you have GPU available
            encode_kwargs={'normalize_embeddings': True}  # BGE models benefit from normalization
        )

        # Initialize LLM. Model IDs come from settings (GEMINI_MODEL /
        # GEMINI_MODEL_ADVANCED) — Google retires generations per account, so
        # hard-coding one here has already bitten us twice (2.0 -> 2.5 -> 3.x).
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            api_key=settings.GOOGLE_API_KEY,
            temperature=0.7,
            max_output_tokens=32768
        )

        self.llm_advanced = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL_ADVANCED,
            api_key=settings.GOOGLE_API_KEY,
            temperature=0.7,
            max_output_tokens=32768  # Increased from 4096 to handle large data separation (3000+ words)
        )

        # Batching configuration for embeddings
        self.embedding_batch_size = settings.EMBEDDING_BATCH_SIZE

    def _get_db_connection(self):
        """Create a database connection"""
        try:
            conn = psycopg2.connect(**settings.db_config)
            return conn
        except Exception as e:
            print(f"[DB_ERROR] Failed to connect to database: {e}")
            raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

    def _embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text using BGE model"""
        try:
            embeddings = self.embeddings.embed_documents([text])
            return embeddings[0]  # Return first (and only) embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")

    async def _embed_text_async(self, text: str) -> List[float]:
        """Generate embedding asynchronously without blocking the event loop"""
        try:
            loop = asyncio.get_event_loop()
            # Run the blocking embedding operation in a thread pool
            embedding = await loop.run_in_executor(
                None,  # Uses default ThreadPoolExecutor
                lambda: self.embeddings.embed_documents([text])[0]
            )
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")
