import re
from typing import List, Dict
from fastapi import HTTPException
from app.services.base_service import BaseService
from app.services.database_service import database_service
from app.models.schemas import SimilaritySearchRequest, SimilaritySearchResponse, SimilarityResult

class VectorService(BaseService):
    def __init__(self):
        super().__init__()

    def _filter_orphaned_vectors(self, relevant_docs: list) -> list:
        """Filter out orphaned vectors from deleted contexts"""
        if not relevant_docs:
            return relevant_docs

        # Extract unique context IDs from all documents
        context_ids = set()
        for doc in relevant_docs:
            metadata = doc.get('metadata', {})
            context_id = metadata.get('contextId') or metadata.get('fileId')
            if context_id:
                context_ids.add(context_id)

        # Batch validate all unique context IDs (single DB query for all IDs!)
        valid_context_ids = database_service.batch_context_exists(list(context_ids))

        # Filter documents based on validated context IDs
        validated_docs = []
        orphaned_count = 0

        for doc in relevant_docs:
            metadata = doc.get('metadata', {})
            context_id = metadata.get('contextId') or metadata.get('fileId')

            if context_id in valid_context_ids:
                validated_docs.append(doc)
            else:
                orphaned_count += 1
                if orphaned_count == 1:  # Only log first orphaned vector to reduce noise
                    print(f"[VECTOR_SERVICE] ⚠ Found orphaned vectors from deleted context(s)")

        if orphaned_count > 0:
            print(f"[VECTOR_SERVICE] Filtered out {orphaned_count} orphaned vectors from {len(context_ids) - len(valid_context_ids)} deleted context(s)")

        return validated_docs
    
    def store_vectors(self, vectors_data: List[dict]):
        """Store multiple vectors in S3 Vectors"""
        try:
            # Format vectors according to S3 Vectors API specification
            formatted_vectors = []
            for vector_data in vectors_data:
                formatted_vector = {
                    "key": vector_data["id"],
                    "data": {"float32": vector_data["vector"]},
                    "metadata": vector_data["metadata"]
                }
                formatted_vectors.append(formatted_vector)
            
            self.s3vectors_client.put_vectors(
                vectorBucketName=self.vector_bucket_name,
                indexName=self.vector_index_name,
                vectors=formatted_vectors
            )
        except Exception as e:
            print(f"Error storing vectors: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to store vectors: {str(e)}")
    
    def query_vectors(self, query_vector: List[float], top_k: int = 5, filter_metadata: dict = None) -> List[dict]:
        """Query vectors from S3 Vectors with metadata filtering"""
        try:
            query_params = {
                'vectorBucketName': self.vector_bucket_name,
                'indexName': self.vector_index_name,
                'queryVector': {'float32': query_vector},
                'topK': top_k,
                'returnDistance': True,
                'returnMetadata': True
            }
            
            # Add server-side filtering if provided
            if filter_metadata:
                # Convert simple key-value filters to S3 Vectors format
                conditions = []
                for key, value in filter_metadata.items():
                    conditions.append({key: {"$eq": value}})
                
                # If multiple conditions, combine with $and
                if len(conditions) > 1:
                    query_params['filter'] = {"$and": conditions}
                else:
                    query_params['filter'] = conditions[0]
                    
                print(f"Using S3 filter: {query_params['filter']}")
            
            response = self.s3vectors_client.query_vectors(**query_params)
            vectors = response.get('vectors', [])
            print(f"Retrieved {len(vectors)} vectors")
            
            return vectors
            
        except Exception as e:
            print(f"Error querying vectors: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to query vectors: {str(e)}")
    
    def similarity_search(self, search_request: SimilaritySearchRequest, chunk_content_store: dict = None) -> SimilaritySearchResponse:
        """
        Perform similarity search without LLM processing
        """
        try:
            # Prepare filter for user-specific contexts
            filter_dict = {
                "userId": search_request.userId,
                "profileId": search_request.profileId,
            }

            # Search for relevant contexts
            relevant_docs = self.query_vectors(
                query_vector=self._embed_text(search_request.query),
                top_k=search_request.k,
                filter_metadata=filter_dict
            )

            # Filter out orphaned vectors from deleted contexts
            relevant_docs = self._filter_orphaned_vectors(relevant_docs)
            # Format results
            results = []
            for doc in relevant_docs:
                doc_id = doc.get('key', '')
                distance = doc.get('distance', 0.0)
                
                # Calculate similarity score (1 - distance for cosine similarity)
                similarity_score = max(0.0, 1.0 - distance)
                
                # Try to get full content (3-tier retrieval)
                content = ""
                if chunk_content_store and doc_id in chunk_content_store:
                    content = chunk_content_store[doc_id]
                elif doc.get('metadata', {}).get('content'):
                    content = doc['metadata']['content']
                else:
                    content = f"Content from {doc['metadata'].get('fileName', 'Unknown')} - Chunk {doc['metadata'].get('chunkIndex', 'Unknown')}"

                # Strip legacy "Profile ID: ..." prefix
                if content:
                    content = re.sub(r'Profile ID: [a-f0-9-]+\n?', '', content)
                
                results.append(SimilarityResult(
                    content=content,
                    metadata=doc.get('metadata', {}),
                    distance=distance,
                    similarity_score=similarity_score
                ))
            
            return SimilaritySearchResponse(
                query=search_request.query,
                userId=search_request.userId,
                profileId=search_request.profileId,
                total_results=len(results),
                results=results
            )
            
        except Exception as e:
            print(f"[ERROR] Failed to perform similarity search: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error performing similarity search: {str(e)}")
    
    def get_vectors_by_keys(self, keys: List[str]) -> List[dict]:
        """
        Fetch vectors directly by their keys using S3 Vectors GetVectors API.
        Batches requests in groups of 20 (S3 Vectors limit per call).
        Returns list of vectors with metadata (no embedding data).
        """
        if not keys:
            return []

        all_vectors = []
        batch_size = 20  # S3 Vectors GetVectors limit

        for i in range(0, len(keys), batch_size):
            batch = keys[i:i + batch_size]
            try:
                response = self.s3vectors_client.get_vectors(
                    vectorBucketName=self.vector_bucket_name,
                    indexName=self.vector_index_name,
                    keys=batch,
                    returnData=False,
                    returnMetadata=True
                )
                vectors = response.get('vectors', [])
                all_vectors.extend(vectors)
            except Exception as e:
                print(f"[GET_VECTORS_BY_KEYS] Batch {i // batch_size + 1} failed: {e}")

        return all_vectors

    def get_vectors_by_pattern(self, context_id: str, start_chunk: int = 0, max_chunks: int = 20) -> tuple:
        """
        Fallback: fetch vectors using the {contextId}_chunk_{i} naming pattern.
        Probes in batches and stops when consecutive batches return nothing.

        Returns:
            tuple: (vectors_list, total_chunks_found)
        """
        # First, discover total chunk count by probing from 0
        all_known_keys = []
        probe_batch_size = 20
        chunk_index = 0
        max_consecutive_misses = 3
        consecutive_empty_batches = 0

        while consecutive_empty_batches < max_consecutive_misses:
            keys = [f"{context_id}_chunk_{chunk_index + j}" for j in range(probe_batch_size)]
            chunk_index += probe_batch_size

            try:
                response = self.s3vectors_client.get_vectors(
                    vectorBucketName=self.vector_bucket_name,
                    indexName=self.vector_index_name,
                    keys=keys,
                    returnData=False,
                    returnMetadata=False
                )
                found = response.get('vectors', [])

                if found:
                    all_known_keys.extend([v.get('key') for v in found])
                    consecutive_empty_batches = 0
                else:
                    consecutive_empty_batches += 1
            except Exception as e:
                print(f"[GET_VECTORS_PATTERN] Discovery batch failed: {e}")
                consecutive_empty_batches += 1

        total_chunks = len(all_known_keys)

        if total_chunks == 0:
            return [], 0

        # Now fetch only the requested page with full metadata
        page_keys = all_known_keys[start_chunk:start_chunk + max_chunks]
        vectors = self.get_vectors_by_keys(page_keys) if page_keys else []

        print(f"[GET_VECTORS_PATTERN] Total: {total_chunks}, returned {len(vectors)} (startChunk={start_chunk}, limit={max_chunks})")
        return vectors, total_chunks

    def delete_vectors_by_context(self, context_id: str, vector_ids: list = None) -> dict:
        """
        Delete all vectors associated with a specific context/file

        Args:
            context_id: The context/file ID
            vector_ids: Optional list of vector IDs from database (preferred method)

        Returns information about the deletion operation
        """
        try:
            print(f"[DELETE_VECTORS] Starting deletion for contextId: {context_id}")

            # Prefer using stored vector IDs from database (much faster and guaranteed complete)
            if vector_ids:
                print(f"[DELETE_VECTORS] Using stored vector IDs from database ({len(vector_ids)} vectors)")
                vector_keys = vector_ids
            else:
                # Fallback: probe using {contextId}_chunk_{i} naming pattern
                print(f"[DELETE_VECTORS] No stored vector IDs. Probing chunk pattern to discover keys...")

                probe_batch_size = 20
                chunk_index = 0
                max_consecutive_misses = 3
                consecutive_empty_batches = 0
                vector_keys = []

                while consecutive_empty_batches < max_consecutive_misses:
                    keys = [f"{context_id}_chunk_{chunk_index + j}" for j in range(probe_batch_size)]
                    chunk_index += probe_batch_size

                    try:
                        response = self.s3vectors_client.get_vectors(
                            vectorBucketName=self.vector_bucket_name,
                            indexName=self.vector_index_name,
                            keys=keys,
                            returnData=False,
                            returnMetadata=False
                        )
                        found = [v.get('key') for v in response.get('vectors', []) if v.get('key')]

                        if found:
                            vector_keys.extend(found)
                            consecutive_empty_batches = 0
                            print(f"[DELETE_VECTORS] Probe batch {chunk_index // probe_batch_size}: found {len(found)} keys (total: {len(vector_keys)})")
                        else:
                            consecutive_empty_batches += 1
                    except Exception as e:
                        print(f"[DELETE_VECTORS] Probe batch failed: {e}")
                        consecutive_empty_batches += 1

                if vector_keys:
                    print(f"[DELETE_VECTORS] Pattern probe discovered {len(vector_keys)} vectors")
                else:
                    print(f"[DELETE_VECTORS] No vectors found for contextId: {context_id}")
                    return {
                        "deleted_count": 0,
                        "message": "No vectors found for this context"
                    }

            if not vector_keys:
                print(f"[DELETE_VECTORS] No vector keys to delete")
                return {
                    "deleted_count": 0,
                    "message": "No vector keys found"
                }

            print(f"[DELETE_VECTORS] Deleting {len(vector_keys)} vectors from S3...")

            # Delete vectors from S3 Vectors in batches (safe approach)
            import time
            batch_size = 100
            deleted_count = 0
            total_batches = (len(vector_keys) + batch_size - 1) // batch_size

            deletion_start_time = time.time()
            print(f"[DELETE_VECTORS] Starting batch deletion: {total_batches} batches of {batch_size}")

            for i in range(0, len(vector_keys), batch_size):
                batch_num = i // batch_size + 1
                batch = vector_keys[i:i+batch_size]

                batch_start_time = time.time()
                try:
                    # Call S3 delete_vectors API
                    response = self.s3vectors_client.delete_vectors(
                        vectorBucketName=self.vector_bucket_name,
                        indexName=self.vector_index_name,
                        keys=batch
                    )
                    batch_elapsed = time.time() - batch_start_time
                    deleted_count += len(batch)

                    # Log the response to understand what S3 returns
                    print(f"[DELETE_VECTORS] Batch {batch_num}/{total_batches}: Deleted {len(batch)} vectors in {batch_elapsed:.2f}s (total: {deleted_count}/{len(vector_keys)})")
                    print(f"[DELETE_VECTORS] S3 Response: {response}")
                    print(f"[DELETE_VECTORS] Response type: {type(response)}")
                    if isinstance(response, dict):
                        print(f"[DELETE_VECTORS] Response keys: {response.keys()}")
                        for key, value in response.items():
                            print(f"[DELETE_VECTORS]   {key}: {value}")

                except Exception as delete_error:
                    print(f"[DELETE_VECTORS] Error during batch {batch_num}/{total_batches} deletion: {delete_error}")
                    print(f"[DELETE_VECTORS] Error type: {type(delete_error)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to delete vectors batch from S3: {str(delete_error)}"
                    )

            total_elapsed = time.time() - deletion_start_time
            avg_time_per_batch = total_elapsed / total_batches if total_batches > 0 else 0
            print(f"[DELETE_VECTORS] Successfully deleted {deleted_count} vectors in {total_elapsed:.2f}s")
            print(f"[DELETE_VECTORS] Performance: {total_batches} batches, avg {avg_time_per_batch:.2f}s per batch")

            return {
                "deleted_count": deleted_count,
                "message": f"Successfully deleted {deleted_count} vectors",
                "vector_keys": vector_keys
            }

        except HTTPException:
            raise
        except Exception as e:
            print(f"[ERROR] Failed to delete vectors: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete vectors: {str(e)}"
            )
    
    def get_all_vectors_by_user_and_profile(self, user_id: str, profile_id: str) -> List[dict]:
        """
        Get all vectors associated with a specific userId and profileId
        Returns list of vectors with their metadata

        Since S3 Vectors ListVectors API doesn't support metadata filtering,
        we use an improved query_vectors approach with multiple diverse queries
        to ensure complete retrieval of all vectors.
        """
        try:
            print(f"[GET_ALL_VECTORS] Getting all vectors for userId: {user_id}, profileId: {profile_id}")

            all_vectors = []
            seen_vector_ids = set()

            # Prepare filter for user-specific contexts
            filter_dict = {
                "userId": user_id,
                "profileId": profile_id,
            }

            # Use an improved strategy to retrieve ALL vectors
            # Since query_vectors has a topK limit, we use multiple diverse queries
            MAX_TOP_K = 30  # S3 Vectors limit

            # Create a diverse set of query embeddings
            diverse_queries = [
                "document content text information",
                "data analysis statistics numbers",
                "technical code implementation",
                "business strategy planning",
                "creative design interface",
                "research science methodology",
                "process workflow system",
                "product feature functionality",
                "user experience interaction",
                "security privacy compliance",
            ]

            # Add random queries for more diversity
            import random
            for i in range(40):  # More attempts for profile-wide deletion
                random_query = f"query_{i}_{random.randint(1000, 9999)}_{user_id}_{profile_id}"
                diverse_queries.append(random_query)

            print(f"[GET_ALL_VECTORS] Using {len(diverse_queries)} diverse queries to ensure complete retrieval")

            consecutive_empty_rounds = 0
            max_empty_rounds = 8  # More tolerance for profile-wide retrieval

            for idx, query_text in enumerate(diverse_queries):
                batch_vectors = self.query_vectors(
                    query_vector=self._embed_text(query_text),
                    top_k=MAX_TOP_K,
                    filter_metadata=filter_dict
                )

                new_vectors_found = 0
                for vector in batch_vectors:
                    vector_id = vector.get('key', '')
                    if vector_id and vector_id not in seen_vector_ids:
                        all_vectors.append(vector)
                        seen_vector_ids.add(vector_id)
                        new_vectors_found += 1

                if new_vectors_found > 0:
                    consecutive_empty_rounds = 0
                    print(f"[GET_ALL_VECTORS] Query {idx + 1}/{len(diverse_queries)}: Found {new_vectors_found} new vectors (total: {len(all_vectors)})")
                else:
                    consecutive_empty_rounds += 1
                    if consecutive_empty_rounds >= max_empty_rounds:
                        print(f"[GET_ALL_VECTORS] No new vectors found in {max_empty_rounds} consecutive queries. Stopping early.")
                        break

            print(f"[GET_ALL_VECTORS] Successfully retrieved {len(all_vectors)} total vectors")

            return all_vectors

        except Exception as e:
            print(f"[ERROR] Failed to get all vectors: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get all vectors: {str(e)}"
            )
    
    def delete_all_vectors_by_user_and_profile(self, user_id: str, profile_id: str) -> dict:
        """
        Delete all vectors associated with a specific userId and profileId
        Returns information about the deletion operation
        """
        try:
            print(f"[DELETE_ALL_VECTORS] Starting deletion for userId: {user_id}, profileId: {profile_id}")
            
            # Get all vectors for this user and profile
            vectors_to_delete = self.get_all_vectors_by_user_and_profile(user_id, profile_id)
            
            if not vectors_to_delete:
                print(f"[DELETE_ALL_VECTORS] No vectors found for userId: {user_id}, profileId: {profile_id}")
                return {
                    "deleted_count": 0,
                    "message": "No vectors found for this user and profile",
                    "vector_keys": [],
                    "context_ids": []
                }
            
            # Extract vector keys (IDs) to delete and collect unique context IDs
            vector_keys = []
            context_ids = set()
            
            for vec in vectors_to_delete:
                key = vec.get('key')
                if key:
                    vector_keys.append(key)
                
                # Collect context IDs from metadata
                metadata = vec.get('metadata', {})
                context_id = metadata.get('contextId') or metadata.get('fileId')
                if context_id:
                    context_ids.add(context_id)
            
            if not vector_keys:
                print(f"[DELETE_ALL_VECTORS] No vector keys found to delete")
                return {
                    "deleted_count": 0,
                    "message": "No vector keys found",
                    "vector_keys": [],
                    "context_ids": list(context_ids)
                }
            
            print(f"[DELETE_ALL_VECTORS] Found {len(vector_keys)} vectors to delete across {len(context_ids)} contexts")
            
            # Delete vectors from S3 Vectors in batches (S3 may have limits)
            batch_size = 100  # Delete in batches of 100
            deleted_count = 0
            
            for i in range(0, len(vector_keys), batch_size):
                batch = vector_keys[i:i+batch_size]
                try:
                    self.s3vectors_client.delete_vectors(
                        vectorBucketName=self.vector_bucket_name,
                        indexName=self.vector_index_name,
                        keys=batch
                    )
                    deleted_count += len(batch)
                    print(f"[DELETE_ALL_VECTORS] Deleted batch {i//batch_size + 1}: {len(batch)} vectors (total: {deleted_count}/{len(vector_keys)})")
                except Exception as delete_error:
                    print(f"[DELETE_ALL_VECTORS] Error during batch {i//batch_size + 1} deletion: {delete_error}")
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Failed to delete vectors batch from S3: {str(delete_error)}"
                    )
            
            print(f"[DELETE_ALL_VECTORS] Successfully deleted {deleted_count} vectors")
            
            return {
                "deleted_count": deleted_count,
                "message": f"Successfully deleted {deleted_count} vectors from {len(context_ids)} contexts",
                "vector_keys": vector_keys,
                "context_ids": list(context_ids)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"[ERROR] Failed to delete all vectors: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to delete all vectors: {str(e)}"
            )

# Create vector service instance
vector_service = VectorService() 