# async def _retrieve_relevant_topic_segments(
#     self,
#     current_query: str,
#     topic_segments: List[dict],
#     top_k: int = 2
# ) -> List[dict]:
#     """
#     Retrieve most relevant topic segments for the current query using semantic search.
    
#     Args:
#         current_query: The user's current question
#         top_k: Number of relevant segments to retrieve
        
#     Returns:
#         List of relevant topic segments sorted by relevance
#     """
#     if not topic_segments:
#         return []
    
#     print(f"[TOPIC_RETRIEVAL] Retrieving relevant segments for query: {current_query[:50]}...")
    
#     # Get embedding for current query
#     query_embedding = self._embed_text(current_query)
    
#     # Calculate similarity scores for all segments
#     segment_scores = []
#     for segment in topic_segments:
#         similarity = np.dot(query_embedding, segment["embedding"])
#         segment_scores.append({
#             "segment": segment,
#             "relevance_score": float(similarity)
#         })
    
#     # Sort by relevance and get top K
#     segment_scores.sort(key=lambda x: x["relevance_score"], reverse=True)
#     top_segments = segment_scores[:top_k]
    
#     for i, seg in enumerate(top_segments):
#         print(f"[TOPIC_RETRIEVAL] Segment {seg['segment']['segment_id']}: "
#                 f"{seg['segment']['topic_summary'][:40]}... (score: {seg['relevance_score']:.3f})")
    
#     return [seg["segment"] for seg in top_segments]

# async def _optimize_chat_history_with_topics(
#     self,
#     chat_history: List,
#     current_query: str,
#     max_tokens: int = 4000,
#     preserve_recent_turns: int = 3,
#     enable_topic_detection: bool = True,
#     similarity_threshold: float = 0.65
# ) -> dict:
#     """
#     Advanced chat history optimization with topic drift detection.

#     Strategy (Multi-level approach):
#     1. Detect topic segments in conversation
#     2. Keep recent messages (short-term memory)
#     3. Retrieve relevant older topic segments (semantic memory)
#     4. Summarize irrelevant older segments (background context)

#     This handles topic switching by:
#     - Identifying when user switches topics
#     - Retrieving context from relevant past topics
#     - Maintaining continuity across topic switches

#     Args:
#         chat_history: List of chat messages
#         current_query: Current user query (to find relevant topics)
#         max_tokens: Maximum tokens to allocate for chat history
#         preserve_recent_turns: Number of recent conversation turns to keep verbatim
#         enable_topic_detection: Whether to use topic segmentation
#         similarity_threshold: Threshold for topic boundary detection

#     Returns:
#         dict with optimized history and topic metadata
#     """
#     if not chat_history:
#         return {
#             "optimized_messages": [],
#             "formatted_history": "",
#             "summary": None,
#             "total_tokens": 0,
#             "optimization_applied": False,
#             "topic_segments": [],
#             "relevant_topics": []
#         }

#     print(f"[TOPIC_OPTIMIZER] Starting optimization with topic detection: {enable_topic_detection}")

#     # If topic detection disabled, fall back to basic optimization
#     if not enable_topic_detection:
#         basic_result = await self._optimize_chat_history(
#             chat_history, max_tokens, preserve_recent_turns, None
#         )
#         basic_result["topic_segments"] = []
#         basic_result["relevant_topics"] = []
#         return basic_result

#     # Normalize chat history
#     normalized_messages = self._normalize_chat_history(chat_history)

#     # Calculate current token usage
#     full_history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in normalized_messages])
#     current_tokens = self._estimate_tokens(full_history_text)

#     print(f"[TOPIC_OPTIMIZER] Total messages: {len(normalized_messages)}, Tokens: {current_tokens}, Max: {max_tokens}")

#     # Detect topic segments
#     topic_segments = await self._detect_topic_segments(
#         chat_history=chat_history,
#         similarity_threshold=similarity_threshold,
#         min_segment_size=2
#     )

#     # Split into recent and older messages
#     recent_count = min(preserve_recent_turns * 2, len(normalized_messages))
#     recent_messages = normalized_messages[-recent_count:] if recent_count > 0 else []
#     older_messages_count = len(normalized_messages) - recent_count

#     recent_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])
#     recent_tokens = self._estimate_tokens(recent_text)

#     print(f"[TOPIC_OPTIMIZER] Recent: {len(recent_messages)} messages ({recent_tokens} tokens)")
#     print(f"[TOPIC_OPTIMIZER] Older: {older_messages_count} messages to process")

#     # If within token limit, return as-is
#     if current_tokens <= max_tokens:
#         print(f"[TOPIC_OPTIMIZER] No optimization needed - within token limit")
#         return {
#             "optimized_messages": normalized_messages,
#             "formatted_history": full_history_text,
#             "summary": None,
#             "total_tokens": current_tokens,
#             "optimization_applied": False,
#             "topic_segments": topic_segments,
#             "relevant_topics": []
#         }

#     # Retrieve relevant topic segments from older conversation
#     # Exclude segments that are in the recent messages
#     older_segments = [seg for seg in topic_segments if seg["end_index"] <= older_messages_count]

#     relevant_segments = await self._retrieve_relevant_topic_segments(
#         current_query=current_query,
#         topic_segments=older_segments,
#         top_k=2  # Get top 2 relevant older topics
#     )

#     # Build optimized context
#     available_tokens = max_tokens - recent_tokens - 500  # Reserve buffer

#     formatted_parts = []
#     included_segments = []

#     # Add relevant topic segments
#     for segment in relevant_segments:
#         segment_tokens = self._estimate_tokens(segment["segment_text"])

#         if segment_tokens <= available_tokens:
#             formatted_parts.append(f"=== Related Past Discussion: {segment['topic_summary']} ===")
#             formatted_parts.append(segment["segment_text"])
#             formatted_parts.append("")
#             available_tokens -= segment_tokens
#             included_segments.append(segment["segment_id"])
#             print(f"[TOPIC_OPTIMIZER] Including relevant segment {segment['segment_id']}: {segment['topic_summary'][:40]}...")

#     # Summarize remaining irrelevant segments if any
#     irrelevant_segments = [seg for seg in older_segments if seg["segment_id"] not in included_segments]

#     if irrelevant_segments and available_tokens > 200:
#         # Create brief summary of irrelevant topics
#         topics_list = [seg["topic_summary"] for seg in irrelevant_segments]
#         background_summary = f"Earlier in the conversation, we also discussed: {', '.join(topics_list)}."

#         if self._estimate_tokens(background_summary) <= available_tokens:
#             formatted_parts.append(f"=== Earlier Topics (Brief) ===")
#             formatted_parts.append(background_summary)
#             formatted_parts.append("")

#     # Add recent conversation
#     formatted_parts.append("=== Recent Conversation ===")
#     for msg in recent_messages:
#         formatted_parts.append(f"{msg['role'].title()}: {msg['content']}")

#     formatted_history = "\n\n".join(formatted_parts)
#     final_tokens = self._estimate_tokens(formatted_history)

#     print(f"[TOPIC_OPTIMIZER] Optimization complete - Final tokens: {final_tokens} (reduced from {current_tokens})")
#     print(f"[TOPIC_OPTIMIZER] Included {len(relevant_segments)} relevant topic segments")

#     return {
#         "optimized_messages": recent_messages,
#         "formatted_history": formatted_history,
#         "summary": None,
#         "total_tokens": final_tokens,
#         "optimization_applied": True,
#         "original_message_count": len(normalized_messages),
#         "kept_message_count": len(recent_messages),
#         "topic_segments": topic_segments,
#         "relevant_topics": [seg["topic_summary"] for seg in relevant_segments],
#         "topic_count": len(topic_segments)
#     }

# async def _extract_topic_summary(self, segment_messages: List[dict]) -> dict:
#     """
#     Extract concise topic summary and keywords from a conversation segment.
    
#     Args:
#         segment_messages: List of messages in the segment
        
#     Returns:
#         dict with summary and keywords
#     """
#     segment_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in segment_messages])
    
#     prompt = f"""Analyze this conversation segment and provide:
#                 1. A very brief topic summary (1 sentence, max 15 words)
#                 2. 3-5 key keywords or concepts

#                 Conversation Segment:
#                 {segment_text}

#                 Respond in this exact format:
#                 SUMMARY: [one sentence]
#                 KEYWORDS: [keyword1, keyword2, keyword3]"""

#     try:
#         response = await self.llm.ainvoke([HumanMessage(content=prompt)])
#         content = response.content
        
#         # Parse response
#         summary = "General conversation"
#         keywords = []
        
#         for line in content.split('\n'):
#             if line.startswith('SUMMARY:'):
#                 summary = line.replace('SUMMARY:', '').strip()
#             elif line.startswith('KEYWORDS:'):
#                 keywords_text = line.replace('KEYWORDS:', '').strip()
#                 keywords = [k.strip() for k in keywords_text.split(',')]
        
#         return {"summary": summary, "keywords": keywords}
    
#     except Exception as e:
#         print(f"[TOPIC_DETECTION] Failed to extract topic summary: {e}")
#         return {"summary": "Conversation segment", "keywords": []}



# async def _detect_topic_segments(
#         self, 
#         chat_history: List,
#         similarity_threshold: float = 0.65,
#         min_segment_size: int = 2
#     ) -> List[dict]:
#         """
#         Detect topic boundaries in conversation using semantic similarity.
        
#         Based on research:
#         - TextTiling algorithm (Hearst, 1997)
#         - Neural topic segmentation (modern approach with embeddings)
#         - Anthropic's topic-based memory
        
#         Strategy:
#         1. Calculate semantic similarity between consecutive message pairs
#         2. Identify topic boundaries where similarity drops below threshold
#         3. Group messages into topic segments
#         4. Extract topic summary and keywords for each segment
        
#         Args:
#             chat_history: List of chat messages
#             similarity_threshold: Similarity threshold for topic boundary (0.6-0.7 recommended)
#             min_segment_size: Minimum messages per segment (avoid micro-segments)
            
#         Returns:
#             List of topic segments with metadata
#         """
#         if not chat_history or len(chat_history) < 2:
#             return []
        
#         print(f"[TOPIC_DETECTION] Starting topic segmentation on {len(chat_history)} messages")
        
#         # Normalize chat history to standard format
#         normalized_messages = self._normalize_chat_history(chat_history)
        
#         if len(normalized_messages) < 2:
#             return []
        
#         # Calculate similarity scores between consecutive message windows
#         # Use sliding window of 2 turns (4 messages) for better context
#         similarities = []
#         window_size = 4
        
#         for i in range(0, len(normalized_messages) - window_size):
#             # Create text from current window and next window
#             current_window = " ".join([msg['content'] for msg in normalized_messages[i:i+window_size]])
#             next_window = " ".join([msg['content'] for msg in normalized_messages[i+2:i+window_size+2]])
            
#             if current_window and next_window:
#                 similarity = self._calculate_topic_similarity(current_window, next_window)
#                 similarities.append({
#                     "index": i + window_size - 1,  # Boundary point
#                     "similarity": similarity
#                 })
#                 print(f"[TOPIC_DETECTION] Window {i}-{i+window_size} vs {i+2}-{i+window_size+2}: {similarity:.3f}")
        
#         # Identify topic boundaries (low similarity = topic change)
#         topic_boundaries = [0]  # Start of conversation
        
#         for i, sim_data in enumerate(similarities):
#             if sim_data["similarity"] < similarity_threshold:
#                 boundary_idx = sim_data["index"]
#                 # Ensure minimum segment size
#                 if boundary_idx - topic_boundaries[-1] >= min_segment_size:
#                     topic_boundaries.append(boundary_idx)
#                     print(f"[TOPIC_DETECTION] Topic boundary detected at message {boundary_idx} (similarity: {sim_data['similarity']:.3f})")
        
#         topic_boundaries.append(len(normalized_messages))  # End of conversation
        
#         # Create topic segments
#         segments = []
#         for i in range(len(topic_boundaries) - 1):
#             start_idx = topic_boundaries[i]
#             end_idx = topic_boundaries[i + 1]
#             segment_messages = normalized_messages[start_idx:end_idx]
            
#             if not segment_messages:
#                 continue
            
#             # Create segment text
#             segment_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in segment_messages])
            
#             # Extract topic summary using LLM
#             topic_summary = await self._extract_topic_summary(segment_messages)
            
#             segments.append({
#                 "segment_id": i,
#                 "start_index": start_idx,
#                 "end_index": end_idx,
#                 "message_count": len(segment_messages),
#                 "messages": segment_messages,
#                 "segment_text": segment_text,
#                 "topic_summary": topic_summary["summary"],
#                 "keywords": topic_summary["keywords"],
#                 "embedding": self._embed_text(segment_text[:1000])  # Embed first 1000 chars for efficiency
#             })
            
#             print(f"[TOPIC_DETECTION] Segment {i}: messages {start_idx}-{end_idx}, topic: {topic_summary['summary'][:50]}...")
        
#         print(f"[TOPIC_DETECTION] Detected {len(segments)} topic segments")
#         return segments
    



# def _calculate_topic_similarity(self, text1: str, text2: str) -> float:
#     """
#     Calculate semantic similarity between two text segments using cosine similarity.
    
#     Args:
#         text1: First text segment
#         text2: Second text segment
        
#     Returns:
#         Similarity score between 0 and 1 (1 = identical, 0 = completely different)
#     """
#     try:
#         # Get embeddings for both texts
#         embedding1 = self._embed_text(text1)
#         embedding2 = self._embed_text(text2)
        
#         # Calculate cosine similarity
#         # Embeddings are already normalized by BGE model (normalize_embeddings=True)
#         similarity = np.dot(embedding1, embedding2)
        
#         return float(similarity)
#     except Exception as e:
#         print(f"[TOPIC_DETECTION] Error calculating similarity: {e}")
#         return 0.5  # Return neutral score on error


