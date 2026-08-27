import os
import re
import asyncio
import tempfile
import httpx
from datetime import datetime
from fastapi import HTTPException, UploadFile

from app.services.base_service import BaseService
from app.services.vector_service import vector_service
from app.services.database_service import database_service
from app.models.schemas import ContextRequest, ContextResponse, FileUploadResponse, AddRagContextRequest, AddRagContextResponse, DeleteContextRequest, DeleteContextResponse, GetContextDataResponse, DeleteAllContextsRequest, DeleteAllContextsResponse
from app.config.settings import settings
from app.utils.file_utils import (
    validate_file_type,
    get_loader_for_file_type
)
from app.utils.text_utils import (
    chunk_content_by_bytes
)
from app.utils.chat_history_utils import (
    optimize_chat_history
)
from app.utils.llm_utils import (
    extract_title_and_description,
    extract_insights_and_summary
)


def get_strategic_sample(documents, max_chars=24000):
    """
    Sample from beginning, middle, and end of document for holistic summary.
    This ensures the AI gets a comprehensive view of the entire document.
    """
    if not documents:
        return ""

    total_docs = len(documents)

    if total_docs <= 3:
        # Small document - use all content
        return "\n\n".join([doc.page_content for doc in documents])

    # Calculate section sizes (divide equally among beginning, middle, end)
    chars_per_section = max_chars // 3

    # Get beginning section (first docs)
    beginning = []
    beginning_chars = 0
    for doc in documents:
        if beginning_chars >= chars_per_section:
            break
        beginning.append(doc.page_content)
        beginning_chars += len(doc.page_content)

    # Get middle section (around midpoint)
    mid_idx = total_docs // 2
    middle = []
    middle_chars = 0
    for doc in documents[max(0, mid_idx - 1):]:
        if middle_chars >= chars_per_section:
            break
        middle.append(doc.page_content)
        middle_chars += len(doc.page_content)

    # Get end section (last docs)
    end = []
    end_chars = 0
    for doc in reversed(documents):
        if end_chars >= chars_per_section:
            break
        end.insert(0, doc.page_content)
        end_chars += len(doc.page_content)

    # Combine with section markers for context
    sections = []
    if beginning:
        sections.append("[BEGINNING OF DOCUMENT]\n" + "\n".join(beginning))
    if middle:
        sections.append("[MIDDLE OF DOCUMENT]\n" + "\n".join(middle))
    if end:
        sections.append("[END OF DOCUMENT]\n" + "\n".join(end))

    return "\n\n".join(sections)


class ContextService(BaseService):
    def __init__(self):
        super().__init__()
        # Reuse the module-level singletons instead of constructing fresh
        # instances: each VectorService() would load the BGE embedding model
        # again (~1.3GB), and DatabaseService only needs Postgres access.
        self.vector_service = vector_service
        self.database_service = database_service
        # Initialize chunk content store for large files
        self.chunk_content_store = {}
        # Backend webhook configuration
        self.backend_api_url = os.getenv('BACKEND_API_URL', '')
        self.backend_api_key = os.getenv('BACKEND_API_KEY', '')

    async def _send_webhook_notification(self, userId: str, contextId: str, status: str, errorMessage: str = None, vectorIds: list = None, processingProgress: int = None):
        """
        Send webhook notification to backend API when file processing completes or progresses

        Args:
            userId: User ID who owns the context
            contextId: Context ID that was processed
            status: Processing status ('completed', 'inprogress', or 'error')
            errorMessage: Error message if status is 'error'
            vectorIds: List of vector IDs stored in vector database
            processingProgress: Progress percentage (0-100)
        """
        try:
            webhook_url = f"{self.backend_api_url}/ai/context/webhook"

            payload = {
                "userId": userId,
                "contextId": contextId,
                "status": status,
            }

            if errorMessage:
                payload["errorMessage"] = errorMessage

            if vectorIds:
                payload["vectorIds"] = vectorIds

            if processingProgress is not None:
                payload["processingProgress"] = processingProgress

            # Add X-API-Key header (consistent with Backend → AI Service pattern)
            headers = {
                'X-API-Key': self.backend_api_key,
                'Content-Type': 'application/json'
            }

            print(f"[WEBHOOK] Sending notification to {webhook_url} for contextId={contextId}, status={status}, progress={processingProgress}")

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook_url, json=payload, headers=headers)

                if response.status_code == 200:
                    print(f"[WEBHOOK] Successfully notified backend for contextId={contextId}")
                else:
                    print(f"[WEBHOOK] Failed to notify backend: status={response.status_code}, response={response.text}")

        except Exception as e:
            # Don't fail the whole process if webhook fails - just log it
            print(f"[WEBHOOK] Error sending webhook notification for contextId={contextId}: {str(e)}")

    async def _process_chunks_in_background(self, content_chunks, fileId, file_metadata, userId):
        """
        Process content chunks and store vectors in the background (runs in thread pool)

        Args:
            content_chunks: List of content strings (already byte-aware chunked)
            fileId: Unique file identifier
            file_metadata: Base metadata for the file
            userId: User ID who owns the context (for webhook notification)
        """
        try:
            print(f"[BACKGROUND_PROCESSING] Starting background processing for {len(content_chunks)} chunks in thread: {fileId}")

            # Generate unique IDs for each chunk and prepare vector data
            vectors_to_store = []

            for i, chunk_content in enumerate(content_chunks):
                try:
                    doc_id = f"{fileId}_chunk_{i}"

                    # Create metadata copy for this chunk with content stored IN metadata
                    # (byte-aware chunking already ensures this fits under 2048 bytes)
                    chunk_metadata = file_metadata.copy()
                    chunk_metadata["content"] = chunk_content
                    chunk_metadata["chunkIndex"] = i

                    # Generate embedding with error handling (async to avoid blocking)
                    try:
                        embedding = await self._embed_text_async(chunk_content)
                    except Exception as embed_error:
                        print(f"[BACKGROUND_PROCESSING] Embedding failed for chunk {i}: {embed_error}")
                        continue  # Skip this chunk but continue processing others

                    vectors_to_store.append({
                        "id": doc_id,
                        "vector": embedding,
                        "metadata": chunk_metadata
                    })

                    # Calculate and send progress updates every 10 chunks or at milestones
                    current_chunk = i + 1
                    total_chunks = len(content_chunks)
                    progress_percentage = int((current_chunk / total_chunks) * 100)

                    # Send progress update every 10 chunks, or at specific milestones (25%, 50%, 75%), or at the end
                    should_update = (
                        current_chunk % 10 == 0 or
                        current_chunk == total_chunks or
                        progress_percentage in [25, 50, 75]
                    )

                    if should_update:
                        print(f"[BACKGROUND_PROCESSING] Progress: {current_chunk}/{total_chunks} chunks ({progress_percentage}%) processed for {fileId}")

                        # Send progress webhook notification
                        try:
                            await self._send_webhook_notification(
                                userId=userId,
                                contextId=fileId,
                                status='inprogress',
                                processingProgress=progress_percentage
                            )
                        except Exception as webhook_error:
                            print(f"[BACKGROUND_PROCESSING] Progress webhook failed: {webhook_error}")
                            # Don't fail processing if webhook fails

                except Exception as chunk_error:
                    print(f"[BACKGROUND_PROCESSING] Failed to process chunk {i}: {chunk_error}")
                    continue  # Skip this chunk but continue processing others
            
            # Store vectors in S3 Vectors
            if vectors_to_store:
                print(f"[BACKGROUND_PROCESSING] Storing {len(vectors_to_store)} vectors in S3 for {fileId}...")
                try:
                    # Collect all vector IDs for webhook notification
                    all_vector_ids = [vec["id"] for vec in vectors_to_store]

                    # Process vectors in batches to avoid overwhelming S3
                    batch_size = 50  # Larger batch size since we're in a separate thread
                    for batch_start in range(0, len(vectors_to_store), batch_size):
                        batch_end = min(batch_start + batch_size, len(vectors_to_store))
                        batch = vectors_to_store[batch_start:batch_end]

                        # Store batch
                        self.vector_service.store_vectors(batch)
                        print(f"[BACKGROUND_PROCESSING] Stored batch {batch_start//batch_size + 1}/{(len(vectors_to_store) + batch_size - 1)//batch_size} for {fileId}")

                    print(f"[BACKGROUND_PROCESSING] Successfully stored all vectors for file {fileId}")

                    # Send webhook notification to backend (success) - backend handles DB updates
                    await self._send_webhook_notification(
                        userId=userId,
                        contextId=fileId,
                        status='completed',
                        vectorIds=all_vector_ids,
                        processingProgress=100
                    )

                except Exception as store_error:
                    print(f"[BACKGROUND_PROCESSING] Vector storage failed for file {fileId}: {store_error}")

                    # Send webhook notification to backend (error) - backend handles DB updates
                    await self._send_webhook_notification(
                        userId=userId,
                        contextId=fileId,
                        status='error',
                        errorMessage=str(store_error)
                    )

                    raise store_error
            else:
                print(f"[BACKGROUND_PROCESSING] No vectors to store for file {fileId}")

                # Send webhook notification to backend (completed with no vectors) - backend handles DB updates
                await self._send_webhook_notification(
                    userId=userId,
                    contextId=fileId,
                    status='completed',
                    vectorIds=[]
                )

        except Exception as e:
            print(f"[BACKGROUND_PROCESSING] Background processing failed for file {fileId}: {str(e)}")

            # Send webhook notification to backend (error) - backend handles DB updates
            await self._send_webhook_notification(
                userId=userId,
                contextId=fileId,
                status='error',
                errorMessage=str(e)
            )
        finally:
            print(f"[BACKGROUND_PROCESSING] Completed processing for file {fileId}")

    async def upload_file(self, file: UploadFile, userId: str, profileId: str, contextId: str = None) -> FileUploadResponse:
        """
        Upload and process a file (TXT or DOCX) with API key validation
        """
        try:
            print(f"[FILE_UPLOAD] User: {userId}, File: {file.filename}, ContextId: {contextId}")
            
            # Validate file type
            file_type = validate_file_type(file.filename)
            
            # Validate file size (10MB limit)
            file_content = await file.read()
            file_size = len(file_content)
            print(f"[FILE_UPLOAD] File size: {file_size / (1024*1024):.2f} MB")

            # Check for empty file early
            if file_size == 0:
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded file is empty. Please upload a file with content."
                )

            if file_size > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE // (1024*1024)}MB"
                )
            
            # Use contextId from backend-api
            fileId = contextId
            current_time = datetime.now()
            print(f"[FILE_UPLOAD] Using fileId: {fileId}")
            
            # Create temporary file for processing
            temp_file_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_type}") as temp_file:
                    temp_file.write(file_content)
                    temp_file_path = temp_file.name
                    print(f"[FILE_UPLOAD] Created temporary file: {temp_file_path}")
                
                # Load document using appropriate LangChain loader with enhanced error handling
                print(f"[FILE_UPLOAD] Loading document with {file_type} loader...")
                try:
                    loader = get_loader_for_file_type(temp_file_path, file_type)
                    documents = loader.load()
                    print(f"[FILE_UPLOAD] Successfully loaded {len(documents)} document(s)")
                except Exception as load_error:
                    print(f"[FILE_UPLOAD] Loader failed: {load_error}")
                    raise Exception(f"Failed to load file content: {str(load_error)}")
                
                if not documents:
                    raise Exception("No content could be extracted from the file")
                
                # Use strategic sampling to get content from beginning, middle, and end
                print(f"[FILE_UPLOAD] Combining document content using strategic sampling...")
                full_content = get_strategic_sample(documents)
                content_length = len(full_content)
                print(f"[FILE_UPLOAD] Total content length: {content_length} characters (from {len(documents)} chunks)")
                
                if content_length == 0:
                    raise Exception("File appears to be empty or content could not be extracted")
                
                # Extract title and description from content
                print(f"[FILE_UPLOAD] Extracting title and description...")
                try:
                    title_and_desc = await extract_title_and_description(llm=self.llm, content=full_content, filename=file.filename)
                    print(f"[FILE_UPLOAD] Extracted title: {title_and_desc['title']}")
                except Exception as title_error:
                    print(f"[FILE_UPLOAD] Title extraction failed: {title_error}")
                    # Use fallback title and description
                    title_and_desc = {
                        "title": file.filename.split('.')[0] if file.filename else "Uploaded Document",
                        "description": "• Content extracted from uploaded document\n• Available for search and retrieval"
                    }
                
                # Validate that we have valid UUIDs before attempting processing
                if userId == "string" or profileId == "string":
                    error_msg = f"Invalid input: userId and profileId must be valid UUIDs, got userId='{userId}', profileId='{profileId}'"
                    print(f"[FILE_UPLOAD] {error_msg}")
                    raise HTTPException(status_code=400, detail=error_msg)
                # Create base metadata for the file (WITHOUT description to save space)
                file_metadata = {
                    "userId": userId,
                    "profileId": profileId,
                    "fileId": fileId,
                    "fileName": file.filename,
                    "fileType": file_type,
                    "contentType": "file",
                    "title": title_and_desc["title"],
                    # "description": title_and_desc["description"],  # REMOVED - not used during retrieval
                    "createdAt": int(current_time.timestamp()),
                }

                # Combine all document content for byte-aware chunking
                print(f"[FILE_UPLOAD] Combining document content for byte-aware chunking...")
                combined_content = "\n\n".join([doc.page_content for doc in documents])

                # Use byte-aware chunking to ensure each chunk + metadata stays under 2048 bytes
                print(f"[FILE_UPLOAD] Performing byte-aware chunking...")
                try:
                    content_chunks = chunk_content_by_bytes(
                        content=combined_content,
                        metadata=file_metadata,
                        max_total_bytes=2048,
                        safety_buffer=200
                    )
                    print(f"[FILE_UPLOAD] Created {len(content_chunks)} byte-aware chunks")
                except Exception as split_error:
                    print(f"[FILE_UPLOAD] Byte-aware chunking failed: {split_error}")
                    raise Exception(f"Failed to chunk document: {str(split_error)}")

                if not content_chunks:
                    raise Exception("Document chunking resulted in no chunks")
                
                # Return immediately, process chunks in background
                print(f"[FILE_UPLOAD] Returning FileUploadResponse immediately. Chunks will be processed in background.")

                # Create FileUploadResponse to return immediately
                response = FileUploadResponse(
                    message=f"Successfully uploaded: {file.filename}. Processing {len(content_chunks)} chunks in background.",
                    contextId=fileId,
                    fileName=file.filename,
                    fileType=file_type,
                    chunks=len(content_chunks),
                    createdAt=current_time.strftime('%Y-%m-%d %H:%M:%S'),
                    extractedTitle=title_and_desc["title"],
                    extractedDescription=title_and_desc["description"]
                )

                # Start background processing (don't await it)
                asyncio.create_task(
                    self._process_chunks_in_background(
                        content_chunks,
                        fileId,
                        file_metadata,
                        userId  # Pass userId for webhook notification
                    )
                )
                
                return response
                
            finally:
                # Clean up temporary file
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.unlink(temp_file_path)
                        print(f"[FILE_UPLOAD] Cleaned up temporary file: {temp_file_path}")
                    except Exception as cleanup_error:
                        print(f"[FILE_UPLOAD] Failed to cleanup temporary file: {cleanup_error}")
                
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            print(f"[ERROR] Failed to upload file for user {userId}: {str(e)}")
            # Provide more specific error message based on the error
            if "encoding" in str(e).lower() or "decode" in str(e).lower():
                error_msg = f"File encoding issue: {str(e)}. Please ensure the file is saved in UTF-8 encoding or try a different file format."
            elif "load" in str(e).lower():
                error_msg = f"File loading error: {str(e)}. The file format may be corrupted or unsupported."
            elif "embedding" in str(e).lower():
                error_msg = f"Text processing error: {str(e)}. Please try with a smaller file or different content."
            elif "vector" in str(e).lower() or "store" in str(e).lower():
                error_msg = f"Storage error: {str(e)}. Please try again or contact support if the issue persists."
            else:
                error_msg = f"Error processing file: {str(e)}"
            
            raise HTTPException(status_code=500, detail=error_msg)

    async def add_context(self, context_request: ContextRequest) -> ContextResponse:
        """
        Add a new context to the notebook system with API key validation
        """
        try:
            # Extract a meaningful title and description from the context using LLM
            title_and_desc = await extract_title_and_description(llm = self.llm, content = context_request.context)

            # Log the authenticated request
            print(f"[CONTEXT_ADD] User: {context_request.userId}, Title: {title_and_desc['title']}")

            # Use contextId from backend-api
            contextId = context_request.contextId
            current_time = datetime.now()
            print(f"[CONTEXT_ADD] Using contextId: {contextId}")
            
            # Prepare context text with title and metadata
            formatted_context = f"""
            Title: {title_and_desc['title']}
            Content: {context_request.context}
            """
            
            # Create metadata for the context (WITHOUT description to save space)
            context_metadata = {
                "userId": context_request.userId,
                "contextId": contextId,
                "title": title_and_desc['title'],
                # "description": title_and_desc['description'],  # REMOVED - not used during retrieval
                "profileId": context_request.profileId,
                "createdAt": int(current_time.timestamp()),
                "contentType": "manual_context",  # Distinguish from file uploads
            }

            # Use byte-aware chunking to ensure each chunk + metadata stays under 2048 bytes
            content_chunks = chunk_content_by_bytes(
                content=formatted_context,
                metadata=context_metadata,
                max_total_bytes=2048,
                safety_buffer=200
            )

            print(f"[CONTEXT_ADD] Created {len(content_chunks)} byte-aware chunks")

            # Prepare vector data for storage
            vectors_to_store = []
            for i, chunk_content in enumerate(content_chunks):
                doc_id = f"{contextId}_chunk_{i}"

                # Create metadata copy for this chunk with content
                chunk_metadata = context_metadata.copy()
                chunk_metadata["content"] = chunk_content
                chunk_metadata["chunkIndex"] = i

                vectors_to_store.append({
                    "id": doc_id,
                    "vector": self._embed_text(chunk_content),
                    "metadata": chunk_metadata
                })

            # Store vectors in S3 Vectors
            self.vector_service.store_vectors(vectors_to_store)

            # Collect vector IDs for response
            vector_ids = [vec["id"] for vec in vectors_to_store]

            return ContextResponse(
                message=f"Successfully added context: {title_and_desc['title']}",
                contextId=contextId,
                chunks=len(content_chunks),
                createdAt=current_time.strftime('%Y-%m-%d %H:%M:%S'),
                extractedTitle=title_and_desc['title'],
                extractedDescription=title_and_desc['description'],
                vectorIds=vector_ids
            )

        except Exception as e:
            print(f"[ERROR] Failed to add context for user {context_request.userId}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error adding context: {str(e)}")

    async def add_rag_context(self, rag_request: AddRagContextRequest) -> AddRagContextResponse:
        """
        Process chat history to extract insights and user information, then save to vectorDB
        """
        try:
            total_tokens_used = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            }
            # Convert chat history to readable text format
            optimized_history = await optimize_chat_history(
                llm=self.llm,
                chat_history=rag_request.chatHistory,
                max_tokens=4000,
                preserve_recent_turns=3,
                total_tokens_used=total_tokens_used
            )
            chat_text = optimized_history["formatted_history"]
            total_tokens_used = optimized_history["total_tokens_used"]
            
            # Extract insights and user information using LLM
            insights_and_summary = await extract_insights_and_summary(llm = self.llm_advanced, chat_text = chat_text)

            # Log the authenticated request
            print(f"[RAG_CONTEXT_ADD] User: {rag_request.userId}, Chat messages: {len(rag_request.chatHistory)}")

            # Use contextId from backend-api
            contextId = rag_request.contextId
            current_time = datetime.now()
            print(f"[RAG_CONTEXT_ADD] Using contextId: {contextId}")
            
            # Prepare context text with insights and user info
            formatted_context = f"""
            Title: {insights_and_summary['title']}
            Content: {insights_and_summary['insights']}
            """
            
            # Create metadata for the context (WITHOUT description to save space)
            context_metadata = {
                "userId": rag_request.userId,
                "contextId": contextId,
                "title": insights_and_summary['title'],
                # "description": insights_and_summary['description'],  # REMOVED - not used during retrieval
                "profileId": rag_request.profileId,
                "createdAt": int(current_time.timestamp()),
                "contentType": "chat_history",  # Distinguish from other content types
            }

            # Use byte-aware chunking to ensure each chunk + metadata stays under 2048 bytes
            content_chunks = chunk_content_by_bytes(
                content=formatted_context,
                metadata=context_metadata,
                max_total_bytes=2048,
                safety_buffer=200
            )

            print(f"[RAG_CONTEXT_ADD] Created {len(content_chunks)} byte-aware chunks")

            # Prepare vector data for storage
            vectors_to_store = []
            for i, chunk_content in enumerate(content_chunks):
                doc_id = f"{contextId}_chunk_{i}"

                # Create metadata copy for this chunk with content
                chunk_metadata = context_metadata.copy()
                chunk_metadata["content"] = chunk_content
                chunk_metadata["chunkIndex"] = i

                vectors_to_store.append({
                    "id": doc_id,
                    "vector": self._embed_text(chunk_content),
                    "metadata": chunk_metadata
                })

            # Store vectors in S3 Vectors
            self.vector_service.store_vectors(vectors_to_store)

            # Collect vector IDs for response
            vector_ids = [vec["id"] for vec in vectors_to_store]

            return AddRagContextResponse(
                message=f"Successfully processed chat history: {insights_and_summary['title']}",
                contextId=contextId,
                chunks=len(content_chunks),
                createdAt=current_time.strftime('%Y-%m-%d %H:%M:%S'),
                extractedTitle=insights_and_summary['title'],
                extractedDescription=insights_and_summary['description'],
                extractedInsights=insights_and_summary['insights'],
                vectorIds=vector_ids
            )

        except Exception as e:
            print(f"[ERROR] Failed to add rag context for user {rag_request.userId}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing chat history: {str(e)}")

    async def delete_context(self, delete_request: DeleteContextRequest) -> DeleteContextResponse:
        """
        Delete a context and all associated vectors from the system
        """
        try:
            print(f"[DELETE_CONTEXT] User: {delete_request.userId}, ContextId: {delete_request.contextId}")

            # Step 1: Retrieve stored vector IDs from database
            stored_vector_ids = self.database_service.get_vector_ids(delete_request.contextId)

            # Step 2: Delete vectors from S3 Vectors using stored IDs (much faster!)
            deletion_result = self.vector_service.delete_vectors_by_context(
                context_id=delete_request.contextId,
                vector_ids=stored_vector_ids
            )

            deleted_vectors_count = deletion_result.get("deleted_count", 0)
            vector_keys = deletion_result.get("vector_keys", [])
            
            print(f"[DELETE_CONTEXT] Deleted {deleted_vectors_count} vectors from S3")
            
            # Step 2: Clean up chunk_content_store (in-memory cache)
            if hasattr(self, 'chunk_content_store') and self.chunk_content_store:
                removed_from_cache = 0
                for vector_key in vector_keys:
                    if vector_key in self.chunk_content_store:
                        del self.chunk_content_store[vector_key]
                        removed_from_cache += 1
                
                if removed_from_cache > 0:
                    print(f"[DELETE_CONTEXT] Cleaned up {removed_from_cache} chunks from memory cache")
            

            # Construct response
            if deleted_vectors_count > 0:
                message = f" ({deleted_vectors_count} vectors removed)"
            else:
                message = "Context not found or already deleted"
            
            return DeleteContextResponse(
                message=message,
                contextId=delete_request.contextId,
                deletedVectors=deleted_vectors_count,
            )
            

        except Exception as e:
            print(f"[ERROR] Failed to delete context for user {delete_request.userId}: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error deleting context: {str(e)}"
            )
      
    async def get_context_data(self, context_id: str, user_id: str, start_chunk: int = 0, limit: int = 20) -> GetContextDataResponse:
        """
        Get context content with pagination.

        Strategy:
        1. Primary: Fetch vector IDs from DB, slice to requested page, fetch via S3 GetVectors
        2. Fallback: Probe using {contextId}_chunk_{i} pattern for the requested range
        """
        try:
            print(f"[GET_CONTEXT_DATA] User: {user_id}, ContextId: {context_id}, startChunk: {start_chunk}, limit: {limit}")

            total_chunks = 0
            vectors = []

            # Primary: try fetching vector IDs from the database
            stored_vector_ids = self.database_service.get_vector_ids(context_id)

            if stored_vector_ids:
                total_chunks = len(stored_vector_ids)
                # Only fetch the requested page
                page_ids = stored_vector_ids[start_chunk:start_chunk + limit]
                print(f"[GET_CONTEXT_DATA] DB path: {total_chunks} total, fetching chunks {start_chunk}-{start_chunk + len(page_ids) - 1}")
                vectors = self.vector_service.get_vectors_by_keys(page_ids)

            # Fallback: probe using chunk ID naming pattern
            if not vectors:
                print(f"[GET_CONTEXT_DATA] Falling back to pattern probe for {context_id}")
                vectors, total_chunks = self.vector_service.get_vectors_by_pattern(context_id, start_chunk=start_chunk, max_chunks=limit)

            if not vectors:
                raise HTTPException(
                    status_code=404,
                    detail=f"No vectors found for context {context_id}"
                )

            # Extract metadata from first vector (context-level info)
            first_vector_metadata = vectors[0].get('metadata', {})
            title = first_vector_metadata.get('title', 'Untitled')
            content_type = first_vector_metadata.get('contentType', 'unknown')

            # Sort vectors by chunkIndex, then extract and concatenate content
            vectors.sort(key=lambda v: v.get('metadata', {}).get('chunkIndex', 0))

            chunks = []
            for vector in vectors:
                vector_id = vector.get('key', '')
                metadata = vector.get('metadata', {})

                chunk_content = ""
                if hasattr(self, 'chunk_content_store') and vector_id in self.chunk_content_store:
                    chunk_content = self.chunk_content_store[vector_id]
                elif metadata.get('content'):
                    chunk_content = metadata['content']

                if chunk_content:
                    # Strip legacy "Profile ID: ..." from old stored vectors
                    chunk_content = re.sub(r'Profile ID: [a-f0-9-]+\n?', '', chunk_content)
                    chunks.append(chunk_content)

            content = "\n\n".join(chunks)

            # Calculate next chunk cursor
            next_chunk_start = start_chunk + limit
            next_chunk = next_chunk_start if next_chunk_start < total_chunks else None

            print(f"[GET_CONTEXT_DATA] Returned {len(chunks)}/{total_chunks} chunks, nextChunk: {next_chunk}")

            return GetContextDataResponse(
                contextId=context_id,
                title=title,
                contentType=content_type,
                totalChunks=total_chunks,
                content=content,
                nextChunk=next_chunk
            )

        except HTTPException:
            raise
        except Exception as e:
            print(f"[ERROR] Failed to get context data: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error getting context data: {str(e)}"
            )
    
    async def delete_all_contexts(self, delete_request: DeleteAllContextsRequest) -> DeleteAllContextsResponse:
        """
        Delete all contexts and all associated vectors for a given userId and profileId
        """
        try:
            print(f"[DELETE_ALL_CONTEXTS] User: {delete_request.userId}, ProfileId: {delete_request.profileId}")

            # Step 1: Retrieve all stored vector IDs from database
            stored_vector_ids = self.database_service.get_all_vector_ids_by_user_profile(
                user_id=delete_request.userId,
                profile_id=delete_request.profileId
            )

            # Step 2: Delete all vectors from S3 Vectors using stored IDs
            if stored_vector_ids:
                print(f"[DELETE_ALL_CONTEXTS] Using stored vector IDs from database ({len(stored_vector_ids)} vectors)")
                # Delete directly using stored IDs
                try:
                    batch_size = 100
                    deleted_count = 0

                    for i in range(0, len(stored_vector_ids), batch_size):
                        batch = stored_vector_ids[i:i+batch_size]
                        self.vector_service.s3vectors_client.delete_vectors(
                            vectorBucketName=self.vector_service.vector_bucket_name,
                            indexName=self.vector_service.vector_index_name,
                            keys=batch
                        )
                        deleted_count += len(batch)
                        if len(stored_vector_ids) > batch_size:
                            print(f"[DELETE_ALL_CONTEXTS] Deleted batch {i//batch_size + 1}: {len(batch)} vectors (total: {deleted_count}/{len(stored_vector_ids)})")

                    deleted_vectors_count = deleted_count
                    vector_keys = stored_vector_ids
                except Exception as e:
                    print(f"[DELETE_ALL_CONTEXTS] Error deleting vectors: {e}")
                    deleted_vectors_count = 0
                    vector_keys = []
            else:
                # Fallback: Use search method for old contexts
                print(f"[DELETE_ALL_CONTEXTS] No stored vector IDs found. Falling back to search method...")
                deletion_result = self.vector_service.delete_all_vectors_by_user_and_profile(
                    user_id=delete_request.userId,
                    profile_id=delete_request.profileId
                )

                deleted_vectors_count = deletion_result.get("deleted_count", 0)
                vector_keys = deletion_result.get("vector_keys", [])

            print(f"[DELETE_ALL_CONTEXTS] Deleted {deleted_vectors_count} vectors from S3")
            
            # Step 2: Clean up chunk_content_store (in-memory cache)
            if hasattr(self, 'chunk_content_store') and self.chunk_content_store:
                removed_from_cache = 0
                for vector_key in vector_keys:
                    if vector_key in self.chunk_content_store:
                        del self.chunk_content_store[vector_key]
                        removed_from_cache += 1
                
                if removed_from_cache > 0:
                    print(f"[DELETE_ALL_CONTEXTS] Cleaned up {removed_from_cache} chunks from memory cache")
            
            
            # Construct response
            if deleted_vectors_count > 0:
                message = f" ({deleted_vectors_count} vectors removed)"
            else:
                message = "Context not found or already deleted"
            
            return DeleteAllContextsResponse(
                message=message,
                userId=delete_request.userId,
                profileId=delete_request.profileId,
                deletedVectors=deleted_vectors_count
            )
            
        except Exception as e:
            print(f"[ERROR] Failed to delete context for user {delete_request.userId}: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error deleting context: {str(e)}"
            )
    

# Create context service instance
context_service = ContextService() 