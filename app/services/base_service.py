import psycopg2
from psycopg2.extras import RealDictCursor
import boto3
import asyncio
from concurrent.futures import ThreadPoolExecutor
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.tools import tool
from duckduckgo_search import DDGS
from langchain_community.document_loaders import WebBaseLoader
from fastapi import HTTPException
import re
from typing import List, Optional
from app.config.settings import settings

# Google Custom Search API
try:
    from googleapiclient.discovery import build
    GOOGLE_SEARCH_AVAILABLE = True
except ImportError:
    GOOGLE_SEARCH_AVAILABLE = False
    print("[WARNING] google-api-python-client not installed. Google Custom Search will not be available.")


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
        
        # Initialize ThreadPoolExecutor for background processing
        self.thread_pool = ThreadPoolExecutor(
            max_workers=settings.MAX_WORKERS,
            thread_name_prefix="file_processor"
        )
        
        # Initialize HuggingFace BGE embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-large-en-v1.5",
            model_kwargs={'device': 'cpu'},  # Use 'cuda' if you have GPU available
            encode_kwargs={'normalize_embeddings': True}  # BGE models benefit from normalization
        )
        
        # Initialize LLM with tool support
        # gemini-2.0-flash was retired; gemini-2.5-flash is the current generally
        # available fast model. Same family, same multimodal + tool-use surface.
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=settings.GOOGLE_API_KEY,
            temperature=0.7,
            max_output_tokens=32768
        )

        self.llm_advanced = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=settings.GOOGLE_API_KEY,
            temperature=0.7,
            max_output_tokens=32768  # Increased from 4096 to handle large data separation (3000+ words)
        )

        self.llm_gemini3 = ChatGoogleGenerativeAI(
            model="gemini-3-pro-preview",
            api_key=settings.GOOGLE_API_KEY,
            temperature=0.7,
            max_output_tokens=32768,
            include_thoughts=True  # Required for Gemini 3 thought signatures with tool calls
        )

        # Initialize tools
        self.web_search_tool = self._create_web_search_tool()
        self.url_content_tool = self._create_url_content_tool()
        
        # Bind tools to LLM
        self.llm_with_tools = self.llm.bind_tools([self.web_search_tool, self.url_content_tool])

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
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if a string is a valid URL"""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)*[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.?[A-Z]{2,}|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url_pattern.match(url) is not None

    def _extract_urls_from_text(self, text: str) -> List[str]:
        """Extract URLs from text"""
        url_pattern = re.compile(
            r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
            re.IGNORECASE
        )
        return url_pattern.findall(text)
    
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

    def _create_web_search_tool(self):
        """Create a web search tool using Google Custom Search (with DuckDuckGo fallback)"""

        # Check if Google Custom Search is configured
        has_google_search = (
            GOOGLE_SEARCH_AVAILABLE and
            settings.GOOGLE_SEARCH_API_KEY and
            settings.GOOGLE_SEARCH_ENGINE_ID
        )

        # Only log once during initialization
        if not hasattr(BaseService, '_web_search_config_logged'):
            if has_google_search:
                print("[WEB_SEARCH] Google Custom Search API configured")
            else:
                print("[WEB_SEARCH] Using DuckDuckGo fallback (Google Custom Search not configured)")
            BaseService._web_search_config_logged = True

        @tool
        def web_search(query: str) -> str:
            """
            Search the web for current information using Google Custom Search (or DuckDuckGo as fallback).
            Use this tool when you need recent or current information that might not be in the knowledge base.

            Args:
                query: The search query to find information on the web

            Returns:
                String containing search results from the web
            """
            # Try Google Custom Search first if configured
            if has_google_search:
                try:
                    service = build("customsearch", "v1", developerKey=settings.GOOGLE_SEARCH_API_KEY)
                    result = service.cse().list(
                        q=query,
                        cx=settings.GOOGLE_SEARCH_ENGINE_ID,
                        num=5,  # Number of results
                        lr='lang_en',  # Language: English
                        gl='us'  # Geolocation: United States
                    ).execute()

                    items = result.get('items', [])

                    if items:
                        formatted_results = []
                        for i, item in enumerate(items):
                            title = item.get('title', 'No title')
                            snippet = item.get('snippet', 'No description')
                            url = item.get('link', 'No URL')
                            formatted_results.append(f"Title: {title}\nDescription: {snippet}\nURL: {url}")
                        return f"Web search results for '{query}':\n\n" + "\n\n".join(formatted_results)
                    else:
                        return f"No web search results found for '{query}'"

                except Exception as e:
                    # Fall through to DuckDuckGo
                    pass

            # Fallback to DuckDuckGo
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, region='us-en', safesearch='off', max_results=5))
                    if results:
                        formatted_results = []
                        for i, result in enumerate(results):
                            title = result.get('title', 'No title')
                            body = result.get('body', 'No description')
                            url = result.get('href', 'No URL')
                            formatted_results.append(f"Title: {title}\nDescription: {body}\nURL: {url}")
                        return f"Web search results for '{query}':\n\n" + "\n\n".join(formatted_results)
                    else:
                        return f"No web search results found for '{query}'"
            except Exception as e:
                return f"Web search failed: {str(e)}"

        return web_search

    def _create_url_content_tool(self):
        """Create a URL content extraction tool using WebBaseLoader"""
        @tool
        def extract_url_content(url: str) -> str:
            """
            Extract content from a URL/webpage.
            Use this tool when the user provides a URL and wants to analyze or get information from that webpage.
            
            Args:
                url: The URL to extract content from
                
            Returns:
                String containing the extracted content from the webpage
            """
            try:
                # Validate URL format
                if not self._is_valid_url(url):
                    return f"Invalid URL format: {url}"
                
                # Load content using WebBaseLoader
                loader = WebBaseLoader(url)
                documents = loader.load()

                if documents:
                    # Get the main content
                    content = documents[0].page_content
                    metadata = documents[0].metadata
                    
                    # Clean and format the content
                    content = content.strip()
                    if len(content) > 8000:  # Limit content size for token limits
                        content = content[:8000] + "... [Content truncated due to length]"
                    
                    title = metadata.get('title', 'No title')
                    source = metadata.get('source', url)
                    
                    return f"URL Content Extracted from: {source}\nTitle: {title}\n\nContent:\n{content}"
                else:
                    return f"No content could be extracted from URL: {url}"
                    
            except Exception as e:
                return f"Failed to extract content from URL {url}: {str(e)}"
        
        return extract_url_content 