"""
Agentic RAG Service using LangGraph
This service implements a state machine-based RAG system that dynamically decides
which operations to perform based on the query and context.
"""

from typing import TypedDict, Annotated, Sequence, Literal
import operator
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool

from app.services.base_service import BaseService
from app.services.vector_service import VectorService
from app.services.database_service import database_service
from app.utils.chat_history_utils import optimize_chat_history
from app.utils.text_utils import get_chunk_sort_key, parse_query_data_response, trim_to_complete_sentences


class AgenticRAGState(TypedDict):
    """State schema for the agentic RAG workflow"""
    # Input fields
    user_query: str
    original_query: str
    user_id: str
    profile_id: str
    chat_history: list
    context_summary: str
    k: int  # Number of contexts to retrieve
    attach_context_summary: bool
    platform: str

    # Intermediate fields
    query_type: str  # "simple", "vague", "conversational", "complex"
    language: str
    separated_query: str
    separated_data: str
    chat_history_text: str
    enhanced_query: str  # For vague query expansion

    # Retrieval fields
    relevant_docs: list
    context: str
    sources: list

    # Decision flags
    needs_query_expansion: bool
    needs_context_relevance_check: bool
    context_is_relevant: bool
    skip_retrieval: bool
    is_pluto_query: bool  # True if query starts with @pluto
    should_show_context: bool  # True if context should be shown in final prompt

    # Output fields
    optimized_prompt: str
    direct_answer: str  # For @pluto queries - direct answer instead of optimized prompt

    # Token tracking
    total_tokens_used: dict

    # Messages for LLM chain
    messages: Annotated[Sequence[BaseMessage], operator.add]

    # Error tracking
    errors: list


class AgenticRAGService(BaseService):
    """
    Agentic RAG Service that uses LangGraph to create a dynamic, self-correcting RAG pipeline.

    The workflow:
    1. Query Analysis → Classify query type and language
    2. Router → Decide which strategy to use
    3. Query Processing → Expand/refine query if needed
    4. Retrieval → Vector search with dynamic parameters
    5. Relevance Check → Evaluate retrieved context
    6. Prompt Generation → Create optimized final prompt
    """

    def __init__(self):
        super().__init__()
        self.vector_service = VectorService()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine for agentic RAG"""
        workflow = StateGraph(AgenticRAGState)

        # Add nodes
        workflow.add_node("initialize", self._initialize_node)
        workflow.add_node("detect_pluto_query", self._detect_pluto_query_node)
        workflow.add_node("analyze_query", self._analyze_query_node)
        workflow.add_node("optimize_chat_history", self._optimize_chat_history_node)
        workflow.add_node("separate_query_data", self._separate_query_data_node)
        workflow.add_node("expand_vague_query", self._expand_vague_query_node)
        workflow.add_node("retrieve_contexts", self._retrieve_contexts_node)
        workflow.add_node("check_context_in_history", self._check_context_in_history_node)
        workflow.add_node("detect_language", self._detect_language_node)
        workflow.add_node("generate_prompt", self._generate_prompt_node)
        workflow.add_node("generate_direct_answer", self._generate_direct_answer_node)

        # Define edges (workflow)
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "detect_pluto_query")
        
        # Conditional routing after @pluto detection
        workflow.add_conditional_edges(
            "detect_pluto_query",
            self._route_after_pluto_detection,
            {
                "pluto_flow": "optimize_chat_history",
                "normal_flow": "analyze_query"
            }
        )
        
        # Normal flow
        workflow.add_edge("analyze_query", "optimize_chat_history")
        workflow.add_edge("optimize_chat_history", "separate_query_data")

        # Conditional routing based on query type (only for normal flow)
        workflow.add_conditional_edges(
            "separate_query_data",
            self._route_after_separation,
            {
                "expand": "expand_vague_query",
                "retrieve": "retrieve_contexts",
                "skip_retrieval": "detect_language",
                "pluto_retrieve": "retrieve_contexts"  # For @pluto flow after separation
            }
        )

        workflow.add_edge("expand_vague_query", "retrieve_contexts")

        # After retrieval, conditionally route based on query type
        workflow.add_conditional_edges(
            "retrieve_contexts",
            self._route_after_retrieval,
            {
                "check_context_in_history": "check_context_in_history",
                "skip_check": "detect_language",
                "pluto_answer": "detect_language"  # For @pluto flow after retrieval
            }
        )

        workflow.add_edge("check_context_in_history", "detect_language")
        
        # Conditional routing after language detection
        workflow.add_conditional_edges(
            "detect_language",
            self._route_after_language_detection,
            {
                "generate_prompt": "generate_prompt",
                "generate_answer": "generate_direct_answer"
            }
        )
        
        workflow.add_edge("generate_prompt", END)
        workflow.add_edge("generate_direct_answer", END)

        return workflow.compile()

    # ==================== NODE IMPLEMENTATIONS ====================

    def _initialize_node(self, state: AgenticRAGState) -> dict:
        """Initialize the state with default values"""
        print("[AGENTIC_RAG] Initializing workflow")
        return {
            "messages": [],
            "errors": [],
            "total_tokens_used": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            },
            "needs_query_expansion": False,
            "needs_context_relevance_check": True,
            "skip_retrieval": False,
            "is_pluto_query": False,
            "relevant_docs": [],
            "context": "",
            "sources": [],
            "enhanced_query": "",
            "chat_history_text": "",
            "separated_query": state["user_query"],
            "separated_data": "None",
            "original_query": state["user_query"],
            "direct_answer": "",
            "should_show_context": True
        }
    
    def _detect_pluto_query_node(self, state: AgenticRAGState) -> dict:
        """Detect if query starts with @pluto and strip it"""
        print("[AGENTIC_RAG] Detecting @pluto query prefix")
        
        user_query = state["user_query"]
        is_pluto_query = user_query.strip().lower().startswith("@pluto")
        
        if is_pluto_query:
            # Strip @pluto prefix and any following whitespace
            cleaned_query = user_query.strip()[6:].strip()  # Remove "@pluto" (6 chars)
            print("[AGENTIC_RAG] @pluto detected! Query cleaned")

            return {
                "is_pluto_query": True,
                "user_query": cleaned_query,
                "separated_query": cleaned_query
            }
        else:
            print("[AGENTIC_RAG] Normal query (no @pluto prefix)")
            return {"is_pluto_query": False}

    async def _analyze_query_node(self, state: AgenticRAGState) -> dict:
        """Analyze the query to classify its type and characteristics"""
        print("[AGENTIC_RAG] Analyzing query")

        analysis_prompt = f"""Analyze the following user query and classify it:

                            User Query: {state['user_query']}
                            Chat History Length: {len(state.get('chat_history', []))}
                            Context Summary Available: {bool(state.get('context_summary'))}

                            Classify the query type as ONE of:
                            1. "simple" - Clear, specific question that can be answered directly
                            2. "vague" - Unclear, lacks specificity, needs expansion
                            3. "conversational" - Follow-up question referring to previous conversation
                            4. "complex" - Multi-part question requiring comprehensive reasoning

                            Respond with ONLY ONE WORD: simple, vague, conversational, or complex"""

        try:
            response = await self.llm_advanced.ainvoke([HumanMessage(content=analysis_prompt)])
            query_type = response.content.strip().lower()

            # Track tokens
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = response.usage_metadata
                state["total_tokens_used"]["input_tokens"] += usage.get('input_tokens', 0)
                state["total_tokens_used"]["output_tokens"] += usage.get('output_tokens', 0)
                state["total_tokens_used"]["total_tokens"] += usage.get('input_tokens', 0) + usage.get('output_tokens', 0)

            # Validate query type
            if query_type not in ["simple", "vague", "conversational", "complex"]:
                query_type = "simple"  # Default fallback

            print(f"[AGENTIC_RAG] Query classified as: {query_type}")

            return {
                "query_type": query_type,
                "needs_query_expansion": query_type == "vague" and bool(state.get('context_summary'))
            }

        except Exception as e:
            print(f"[ERROR] Query analysis failed: {e}")
            state["errors"].append(f"Query analysis error: {str(e)}")
            return {"query_type": "simple", "needs_query_expansion": False}

    async def _optimize_chat_history_node(self, state: AgenticRAGState) -> dict:
        """Optimize chat history to reduce token usage"""
        print("[AGENTIC_RAG] Optimizing chat history")

        try:
            # Call async function directly (LangGraph supports async nodes)
            optimized_history = await optimize_chat_history(
                llm=self.llm,
                chat_history=state.get("chat_history", []),
                max_tokens=4000,
                preserve_recent_turns=3,
                total_tokens_used=state["total_tokens_used"]
            )

            return {
                "chat_history_text": optimized_history["formatted_history"],
                "total_tokens_used": optimized_history["total_tokens_used"]
            }

        except Exception as e:
            print(f"[ERROR] Chat history optimization failed: {e}")
            state["errors"].append(f"Chat history error: {str(e)}")
            return {"chat_history_text": ""}

    async def _separate_query_data_node(self, state: AgenticRAGState) -> dict:
        """Separate user query from any data they're providing"""
        print("[AGENTIC_RAG] Separating query and data")

        system_message = SystemMessage(content="""You are an expert text analysis assistant specialized in parsing and separating user inputs.

                    Your task:
                    - Separate user input into QUERY (what they're asking) and DATA (what they're providing)
                    - CRITICAL: Return DATA verbatim without any summarization, truncation, or modification
                    - Extract code blocks, examples, or data from queries and move them to DATA section
                    - Use punctuation, newlines, and formatting as separation cues
                    - Identify DATA only if clearly separate information is provided
                    

                    Output requirements:
                    - Always provide a QUERY (the main question or request)
                    - Set DATA to "None" if no data is provided
                    - If DATA is present, return it EXACTLY as provided - do not summarize or truncate
                    - For large articles/content, return the COMPLETE text in DATA""")

        human_message = HumanMessage(content=f"""Analyze and separate the following user input:

                    User Input: {state['user_query']}
                    Separate into:
                    1. QUERY: The question, request, or instruction
                    2. DATA: Any information, code, examples, or data provided

                    Rules:
                    - Move any code blocks or inline code from QUERY to DATA
                    - Use `:`, newlines, or formatting as separation cues
                    - If no data present, set DATA to "None"
                    - If only data (no query), extract the implicit query
                    - Don't force extraction - when uncertain, leave in QUERY

                    CRITICAL INSTRUCTION: If you identify DATA, return it COMPLETELY and VERBATIM. Do NOT summarize, truncate, or modify it in any way.

                    Response format:
                    QUERY: [the question or request]

                    DATA: [the COMPLETE, UNMODIFIED information or "None"]""")

        try:
            response = await self.llm_advanced.ainvoke([system_message, human_message])

            # Track tokens
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = response.usage_metadata
                state["total_tokens_used"]["input_tokens"] += usage.get('input_tokens', 0)
                state["total_tokens_used"]["output_tokens"] += usage.get('output_tokens', 0)
                state["total_tokens_used"]["total_tokens"] += usage.get('input_tokens', 0) + usage.get('output_tokens', 0)

            result = parse_query_data_response(response.content.strip())

            print("[AGENTIC_RAG] Query and data separated")

            return {
                "separated_query": result.get("query", state["user_query"]),
                "separated_data": result.get("data", "None")
            }

        except Exception as e:
            print(f"[ERROR] Query/data separation failed: {e}")
            state["errors"].append(f"Separation error: {str(e)}")
            return {
                "separated_query": state["user_query"],
                "separated_data": "None"
            }

    async def _expand_vague_query_node(self, state: AgenticRAGState) -> dict:
        """Expand vague queries using context summary and chat history"""
        print("[AGENTIC_RAG] Expanding vague query")

        expansion_prompt = f"""Based on the context summary and conversation history,
                        help me understand what the user is asking about and expand their vague query.

                        Context Summary: {state.get('context_summary', 'No context available')}

                        Conversation History:
                        {state.get('chat_history_text', 'No conversation history')}

                        User's Vague Query: {state['separated_query']}

                        Instructions:
                        1. Analyze the query in context
                        2. Infer user's intent
                        3. Provide a more specific, detailed interpretation
                        4. If still unclear, return the original query
                        5. Focus on extracting key concepts and topics

                        Enhanced Query:"""

        try:
            response = await self.llm_advanced.ainvoke([HumanMessage(content=expansion_prompt)])

            # Track tokens
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = response.usage_metadata
                state["total_tokens_used"]["input_tokens"] += usage.get('input_tokens', 0)
                state["total_tokens_used"]["output_tokens"] += usage.get('output_tokens', 0)
                state["total_tokens_used"]["total_tokens"] += usage.get('input_tokens', 0) + usage.get('output_tokens', 0)

            enhanced_query = response.content.strip()

            # Clean up response
            if enhanced_query.startswith("Enhanced Query:"):
                enhanced_query = enhanced_query.replace("Enhanced Query:", "").strip()

            print("[AGENTIC_RAG] Query expansion completed")

            return {"enhanced_query": enhanced_query}

        except Exception as e:
            print(f"[ERROR] Query expansion failed: {e}")
            state["errors"].append(f"Query expansion error: {str(e)}")
            return {"enhanced_query": state["separated_query"]}

    def _retrieve_contexts_node(self, state: AgenticRAGState) -> dict:
        """Retrieve relevant contexts from vector database"""
        print("[AGENTIC_RAG] Retrieving contexts from vector database")

        # Determine which query to use for retrieval
        if state.get("enhanced_query"):
            search_query = state["enhanced_query"]
            print(f"[AGENTIC_RAG] Using enhanced query for search")
        else:
            search_query = state["separated_query"]

        # Prepare filter
        filter_dict = {
            "userId": state["user_id"],
            "profileId": state["profile_id"]
        }

        try:
            # Perform vector search
            relevant_docs = self.vector_service.query_vectors(
                query_vector=self._embed_text(search_query),
                top_k=state.get("k", 5),
                filter_metadata=filter_dict
            )

            print(f"[AGENTIC_RAG] Found {len(relevant_docs)} relevant documents")

            # Validate contexts - filter out orphaned vectors from deleted contexts
            if relevant_docs:
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
                            print(f"[AGENTIC_RAG] ⚠ Found orphaned vectors from deleted context(s)")

                if orphaned_count > 0:
                    print(f"[AGENTIC_RAG] Filtered out {orphaned_count} orphaned vectors from {len(context_ids) - len(valid_context_ids)} deleted context(s)")

                relevant_docs = validated_docs

            # Process retrieved documents
            context = ""
            sources = []

            if relevant_docs:
                # Sort chunks
                sorted_docs = sorted(relevant_docs, key=get_chunk_sort_key)

                # Build context
                context_parts = []
                for doc in sorted_docs:
                    full_content = doc.get('metadata', {}).get('content', '')
                    if full_content:
                        # Remove Profile ID from content
                        import re
                        full_content = re.sub(r'Profile ID: [a-f0-9-]+\n?', '', full_content)
                        context_parts.append(full_content)

                    # Extract source metadata
                    metadata = doc.get('metadata', {})
                    content_type = metadata.get("contentType", "unknown")
                    source_info = {
                        "title": metadata.get("title", "Untitled"),
                        "profileId": metadata.get("profileId", "Unknown"),
                        "contentType": content_type,
                        "createdAt": metadata.get("createdAt", "Unknown")
                    }

                    if content_type == "file":
                        source_info.update({
                            "fileName": metadata.get("fileName", "Unknown"),
                            "fileType": metadata.get("fileType", "Unknown"),
                            "fileId": metadata.get("fileId", "Unknown")
                        })
                    else:
                        source_info["contextId"] = metadata.get("contextId", "Unknown")

                    sources.append(source_info)

                context = "\n\n".join(context_parts)

            return {
                "relevant_docs": relevant_docs,
                "context": context,
                "sources": sources
            }

        except Exception as e:
            print(f"[ERROR] Context retrieval failed: {e}")
            state["errors"].append(f"Retrieval error: {str(e)}")
            return {
                "relevant_docs": [],
                "context": "",
                "sources": []
            }

    async def _check_context_in_history_node(self, state: AgenticRAGState) -> dict:
        """Clean up context and check if it already exists in chat history (merged operation)"""
        print("[AGENTIC_RAG] Cleaning up context and checking history")

        if not state.get("context"):
            print("[AGENTIC_RAG] No context to process, skipping")
            return {"should_show_context": False}

        # Use optimized chat history text from optimize_chat_history node
        # This has already been truncated/summarized to stay within 4000 token limit
        chat_history_text = state.get("chat_history_text", "")

        # If no chat history, just clean the context
        if not chat_history_text:
            print("[AGENTIC_RAG] No chat history - cleaning context only")
            cleanup_prompt = f"""You are an expert text editor specializing in cleaning up and improving text readability.

User Query: {state['separated_query']}

Context: {state['context']}

Instructions:
    - Grammar fix the 'Context' so that it looks like well-formatted, continued text
    - Fix any spelling mistakes, punctuation errors, or grammatical issues
    - Maintain the original meaning and information - do not remove or add content
    - Do not add Title, Headers, or any kind of headings
    - Return the cleaned text enclosed in triple backticks (i.e., ``` ... ```)
"""
        else:
            print("[AGENTIC_RAG] Using optimized chat history from previous node")
            cleanup_prompt = f"""You are an expert at analyzing text content and improving readability.

Retrieved Context:
{state['context']}

Chat History (already optimized/summarized):
{chat_history_text}

Task: Determine if the information in the "Retrieved Context" was already provided by the user in their previous messages.

Instructions:
1. Compare the factual content and information between the retrieved context and user messages
2. If the retrieved context contains information that the user already mentioned in their previous messages:
   - Return exactly: CONTEXT_ALREADY_IN_HISTORY
3. If the retrieved context contains NEW information not present in user's previous messages:
   - Grammar fix the 'Context' so that it looks like well-formatted, continued text
   - Fix any spelling mistakes, punctuation errors, or grammatical issues
   - Maintain the original meaning and information - do not remove or add content
   - Do not add Title, Headers, or any kind of headings
   - Return the cleaned text enclosed in triple backticks (i.e., ``` ... ```)

Focus on semantic meaning, not exact word matching.

Return EITHER:
- CONTEXT_ALREADY_IN_HISTORY (if context was already in user's messages)
- OR the grammar-fixed context in triple backticks (if context is new information)
"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=cleanup_prompt)])

            # Track tokens
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = response.usage_metadata
                state["total_tokens_used"]["input_tokens"] += usage.get('input_tokens', 0)
                state["total_tokens_used"]["output_tokens"] += usage.get('output_tokens', 0)
                state["total_tokens_used"]["total_tokens"] += usage.get('input_tokens', 0) + usage.get('output_tokens', 0)

            result = response.content.strip()

            if "CONTEXT_ALREADY_IN_HISTORY" in result:
                print("[AGENTIC_RAG] Context already exists in chat history - will NOT show context")
                return {
                    "should_show_context": False,
                    "context": ""  # Clear context since it's redundant
                }
            else:
                print("[AGENTIC_RAG] Context is NEW - cleaned and will show context")
                return {
                    "should_show_context": True,
                    "context": result  # Use cleaned context
                }

        except Exception as e:
            print(f"[ERROR] Context cleanup/history check failed: {e}")
            state["errors"].append(f"Context cleanup error: {str(e)}")
            # On error, keep original context and show it
            return {"should_show_context": True}

    async def _detect_language_node(self, state: AgenticRAGState) -> dict:
        """Detect the language of the user's query"""
        print("[AGENTIC_RAG] Detecting query language")

        system_message = SystemMessage(content="""You are a language detection specialist.
                            Identify the language used in the text. For romanized text (e.g., Latin alphabet used for non-Latin languages),
                            return "Roman [Language]" (e.g., "Roman Urdu", "Roman Arabic").
                            Return only the language name or "Roman [Language]" format. No explanations.""")

        human_message = HumanMessage(content=f"""Detect the language:

                            Text: {state['separated_query']}

                            Language:""")

        try:
            response = await self.llm_advanced.ainvoke([system_message, human_message])

            # Track tokens
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = response.usage_metadata
                state["total_tokens_used"]["input_tokens"] += usage.get('input_tokens', 0)
                state["total_tokens_used"]["output_tokens"] += usage.get('output_tokens', 0)
                state["total_tokens_used"]["total_tokens"] += usage.get('input_tokens', 0) + usage.get('output_tokens', 0)

            language = response.content.strip()
            print(f"[AGENTIC_RAG] Detected language: {language}")

            return {"language": language}

        except Exception as e:
            print(f"[ERROR] Language detection failed: {e}")
            state["errors"].append(f"Language detection error: {str(e)}")
            return {"language": "English"}

    async def _generate_prompt_node(self, state: AgenticRAGState) -> dict:
        """Generate the final optimized prompt"""
        print("[AGENTIC_RAG] Generating optimized prompt")

        context_limit = 30000  # Limit context length to avoid token overflow

        # Determine if we should show context based on LLM check
        show_context = state.get("should_show_context", True) and bool(state.get("context"))

        # Prepare data info message
        data = state.get("separated_data", "None")
        if data and len(data) > 20:
            data_info_msg = "The chat agent has access to extra data provided by the user"
        else:
            data_info_msg = "No extra data provided by the user"

        # Build meta prompt based on context
        has_context = state.get('context') and len(state.get('context', '')) > 100

        if len(state.get("chat_history_text", "")) == 0:
            # First message - can show context
            context_instruction = "6. IMPORTANT: The full context will be appended separately, so create a brief prompt that directs the chat agent on how to use it" if has_context else "6. Create a focused prompt based on the query alone"

            # Build context section only if available
            context_section = f"\n\nRetrieved Context: {state.get('context', '')[:context_limit]}" if state.get('context') else ""

            meta_prompt = f"""You are an AI assistant optimizing a system prompt for a chat agent.
                        Based on the following information, create an optimized system prompt that will help an AI assistant provide the best possible response:

                User's Query: {state['separated_query']}

                {context_section}

                {data_info_msg if data_info_msg else ""}

                Generate the optimized prompt in {state.get('language', 'English')}.

                Your task: Generate a clear, focused system prompt that:
                1. IMPORTANT: Defines the AI assistant's role appropriately for this specific query
                2. Analyze the user's query to understand the user's intent and what they're asking for
                3. Focus on extracting key concepts, topics, or areas the user might be interested in
                4. Do not make up information - only work with what's provided in the context
                5. IMPORTANT: Keep the prompt focused - do not repeat or summarize the retrieved context in detail
                {context_instruction}
                7. Do not include any userId or profileId or any kind of id given to you in the system prompt
                8. Write in SECOND PERSON addressing the chat agent: "You are...", "Your task is..."
                9. **CRITICAL**: Before finalizing, review your system prompt to ensure it doesn't change or reinterpret the original meaning of the user's query. The prompt should help answer what was actually asked, not what you think they should have asked.
                10. Response should not contain markdown language for formatting.
                - If you need to highlight or format something important (such as code snippets, raw data, commands, or key values),
                - use triple backticks
                ```
                your-data-or-important-information
                ```
                - Do NOT use markdown headers, bullet points, or blockquotes outside the above guidance.

                Return ONLY the optimized system prompt"""
        else:
            # Follow-up message
            context_instruction = "5. IMPORTANT: The full context will be appended separately, so create a brief prompt that directs the chat agent on how to use it" if has_context else "5. Create a focused prompt based on the query and conversation history"

            # Build context repetition warning conditionally
            context_repetition_warning = ""
            if has_context:
                context_repetition_warning = "\n                - Any repetition or detailed summary of the context (it will be appended separately)"

            # Build context section only if available
            context_section = f"\n\nRetrieved Context: {state.get('context', '')[:context_limit]}" if state.get('context') else ""

            meta_prompt = f"""You are an AI assistant optimizing a system prompt for a chat agent.

                        User's Query: {state['separated_query']}

                        {context_section}

                        Conversation History: {state.get('chat_history_text', 'No history')}
                         IMPORTANT: {data_info_msg}
                         IMPORTANT: The chat agent already has the conversation history. Do not repeat or reference it unnecessarily.
                         IMPORTANT: Generate the optimized prompt in {state.get('language', 'English')}.

                Your task: Generate a clear, focused system prompt that:
                1. First, analyze the relationship between the user's query and the conversation history:
                a) Complex query with relevant history: Query introduces new aspects but builds on previous discussion
                b) Completely different query: Query is unrelated to conversation history

                2. If the query is on a relevant history:
                - IMPORTANT: Define the AI assistant's role appropriately for this specific query
                - Understand the user's intent based on the query and conversation flow
                - Create a system prompt focused on the current query
                - The chat agent already knows the history context, so avoid repeating or referencing it unnecessarily
                - Always focus on the user query and prioritize the query more than the context and chat history
                - IMPORTANT: Keep the prompt brief - do not repeat or summarize the retrieved context in detail

                3. If the query is completely different and unrelated to conversation history:
                - IMPORTANT: Define the AI assistant's role appropriately for this specific query
                - Treat this as a fresh query and do NOT consider the conversation history in your optimization
                - Focus entirely on the new query and any relevant retrieved context
                - Create a brief, directive prompt without repeating context details
                - Do not reference or be influenced by irrelevant conversation history

                4. Do not make up information - only work with what's provided in the context
                {context_instruction}
                6. Do not include any userId or profileId or any kind of id given to you in the system prompt
                7. Remember: The target chat agent has the same conversation history, so avoid redundant context repetition for simple queries
                8. Always focus on the user query and prioritize the query more than the context and chat history.
                9. **CRITICAL**: Before finalizing, review your system prompt to ensure it doesn't change or reinterpret the original meaning of the user's query. The prompt should help answer what was actually asked, not what you think they should have asked.
                10. Response should not contain markdown language for formatting.
                - If you need to highlight or format something important (such as code snippets, raw data, commands, or key values),
                - use triple backticks
                ```
                your-data-or-important-information
                ```
                - Do NOT use markdown headers, bullet points, or blockquotes outside the above guidance.
                
                CRITICAL: Return ONLY the final optimized system prompt text. Do NOT include:
                - Any analysis or explanation of your decision-making process
                - Any meta-commentary about the query type or relationship to history
                - Any phrases like "Optimized System Prompt:" or similar headers
                - Any reasoning about why you chose a particular approach
                - Any assumptions about the data provided by the user along with this query{context_repetition_warning}

                Return the clean system prompt text that can be directly used by the target chat agent."""

        try:
            response = await self.llm_advanced.ainvoke([HumanMessage(content=meta_prompt)])

            # Track tokens
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = response.usage_metadata
                state["total_tokens_used"]["input_tokens"] += usage.get('input_tokens', 0)
                state["total_tokens_used"]["output_tokens"] += usage.get('output_tokens', 0)
                state["total_tokens_used"]["total_tokens"] += usage.get('input_tokens', 0) + usage.get('output_tokens', 0)

            optimized_prompt = response.content.strip()

            # Remove wrapping backticks if LLM added them around the entire prompt
            if optimized_prompt.startswith('```') and optimized_prompt.endswith('```'):
                optimized_prompt = optimized_prompt[3:-3].strip()

            # Append data if present
            platform = state.get("platform", "chatGPT")
            if data and len(data) > 20:
                if platform == "perplexity" or platform == "gemini":
                    optimized_prompt = f"{optimized_prompt}\n\nHere is the specific provided data to process in this prompt:\n{data.replace('```', '').strip()}"
                else:
                    optimized_prompt = f"{optimized_prompt}\n\n```Here is the specific provided data to process in this prompt: {data.replace('```', '').strip()}```"

            # Append context if appropriate
            if show_context and state.get("attach_context_summary", False) and state.get("context") and len(state.get("context", "")) > 100:
                trimmed_context = trim_to_complete_sentences(state["context"].replace('```', '').strip())
                if platform == "perplexity" or platform == "gemini":
                    optimized_prompt = f"{optimized_prompt}\n\nHere is the specific context. IMPORTANT: Only use it as a background information for better understanding. Do not process it as part of the query:\n{trimmed_context}"
                else:
                    optimized_prompt = f"{optimized_prompt}\n\n```Here is the specific context. IMPORTANT: Only use it as a background information for better understanding. Do not process it as part of the query: {trimmed_context}```"

            print("[AGENTIC_RAG] Optimized prompt generated successfully")

            return {"optimized_prompt": optimized_prompt}

        except Exception as e:
            print(f"[ERROR] Prompt generation failed: {e}")
            state["errors"].append(f"Prompt generation error: {str(e)}")
            return {"optimized_prompt": state["separated_query"]}

    async def _generate_direct_answer_node(self, state: AgenticRAGState) -> dict:
        """Generate a direct answer for @pluto queries using chat history and context"""
        print("[AGENTIC_RAG] Generating direct answer for @pluto query")
        
        chat_history_text = state.get("chat_history_text", "")
        context = state.get("context", "")
        query = state.get("separated_query", "")
        language = state.get("language", "English")
        
        # Build system prompt for direct answering
        system_prompt = f"""You are Plurality's AI Memory Assistant (@pluto).

                            ## Your Role:
                            You answer questions ON BEHALF OF THE USER using their personal context and conversation history. Your answers will be given back to another AI (like ChatGPT or Claude) to help them provide personalized responses.

                            ## Critical Understanding:
                            - The user is using you as a "memory bridge" between different AI systems
                            - Your answer becomes the USER'S answer to the other AI's questions
                            - Write as if the user themselves is responding, not as an AI assistant
                            - The other AI will use your response to understand the user's situation and provide tailored help

                            ## Data Provided:
                            ### Previous Conversation History:
                            {chat_history_text if chat_history_text else "No previous conversation."}

                            ### User's Knowledge Base Context:
                            {context if context else "No relevant context found."}

                            ## Instructions:

                            **Answer Style:**
                            - Write in FIRST PERSON as the user (use "I", "my", "we")
                            - Be conversational and natural, not formal or robotic
                            - Match the tone of what a human would say when answering about themselves
                            - Don't use phrases like "Based on your context..." or "According to your history..." — just answer directly

                            **Content Rules:**
                            1. Use ONLY the provided conversation history and context - no external knowledge
                            2. Include specific details when available (names, dates, metrics, project names)
                            3. If information is missing, say so naturally: "I don't have that information stored" or "I haven't tracked that yet"
                            4. Never invent facts not present in the provided data
                            5. Redact sensitive data (passwords, credentials, IDs) with [REDACTED] if present

                            **Response Format:**
                            - Provide a complete, standalone answer
                            - Be concise but include all relevant details the other AI needs
                            - If the question has multiple parts, answer each part
                            - If context is insufficient, state what's missing naturally: "I haven't added information about X yet, but here's what I do have..."

                            **Important Adaptations:**
                            - For factual questions → Give direct, specific answers with supporting details
                            - For preference questions → State preferences clearly with reasoning if available
                            - For historical questions → Reference specific events/dates from context
                            - For task-related questions → Provide all relevant background the other AI needs to help

                            Language: Respond in {language}

                            Remember: You are the user's voice speaking to another AI. Make your answer useful for that AI to understand the user's situation and provide better help."""

                            
        # Build user message
        user_message = f"User Request: {query}"
        
        try:
            response = await self.llm_advanced.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message)
            ])
            
            # Track tokens
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = response.usage_metadata
                state["total_tokens_used"]["input_tokens"] += usage.get('input_tokens', 0)
                state["total_tokens_used"]["output_tokens"] += usage.get('output_tokens', 0)
                state["total_tokens_used"]["total_tokens"] += usage.get('input_tokens', 0) + usage.get('output_tokens', 0)
            
            direct_answer = response.content.strip()
            print(f"[AGENTIC_RAG] Direct answer generated ({len(direct_answer)} chars)")
            
            return {
                "direct_answer": direct_answer,
                "optimized_prompt": direct_answer  # Set optimized_prompt to answer for consistent response format
            }
        
        except Exception as e:
            print(f"[ERROR] Direct answer generation failed: {e}")
            state["errors"].append(f"Direct answer error: {str(e)}")
            fallback_answer = f"I apologize, but I encountered an error while processing your @pluto request: {str(e)}"
            return {
                "direct_answer": fallback_answer,
                "optimized_prompt": fallback_answer
            }

    # ==================== ROUTING FUNCTIONS ====================
    
    def _route_after_pluto_detection(self, state: AgenticRAGState) -> str:
        """Route based on whether query has @pluto prefix"""
        if state.get("is_pluto_query", False):
            print("[AGENTIC_RAG] Routing to @pluto flow")
            return "pluto_flow"
        else:
            print("[AGENTIC_RAG] Routing to normal RAG flow")
            return "normal_flow"

    def _route_after_separation(self, state: AgenticRAGState) -> str:
        """Decide next step after query/data separation"""
        # For @pluto queries, always retrieve contexts
        if state.get("is_pluto_query", False):
            if not state.get("profile_id"):
                print("[AGENTIC_RAG] @pluto query but no profile ID, skipping retrieval")
                return "skip_retrieval"
            print("[AGENTIC_RAG] @pluto query - routing to retrieval")
            return "pluto_retrieve"
        
        # Normal flow
        # If no profile ID, skip retrieval
        if not state.get("profile_id"):
            print("[AGENTIC_RAG] No profile ID, skipping retrieval")
            return "skip_retrieval"

        # If vague query and we have context summary, expand first
        if state.get("needs_query_expansion", False):
            print("[AGENTIC_RAG] Routing to query expansion")
            return "expand"

        # Otherwise proceed to retrieval
        print("[AGENTIC_RAG] Routing to retrieval")
        return "retrieve"

    def _route_after_retrieval(self, state: AgenticRAGState) -> str:
        """Decide whether to check relevance after retrieval"""
        # For @pluto queries, skip relevance check
        if state.get("is_pluto_query", False):
            print("[AGENTIC_RAG] @pluto query - skipping relevance check")
            return "pluto_answer"
        
        # If no docs retrieved, skip relevance check
        if not state.get("relevant_docs"):
            print("[AGENTIC_RAG] No docs retrieved, skipping relevance check")
            return "skip_check"

        # If context history check is needed, do it
        if state.get("needs_context_relevance_check", True):
            print("[AGENTIC_RAG] Routing to check context in history")
            return "check_context_in_history"

        # Otherwise skip
        print("[AGENTIC_RAG] Skipping context history check")
        return "skip_check"
    
    def _route_after_language_detection(self, state: AgenticRAGState) -> str:
        """Decide whether to generate normal prompt or direct answer"""
        # For @pluto queries, generate direct answer
        if state.get("is_pluto_query", False):
            print("[AGENTIC_RAG] @pluto query - routing to direct answer generation")
            return "generate_answer"
        
        # Normal flow - generate optimized prompt
        print("[AGENTIC_RAG] Normal query - routing to prompt generation")
        return "generate_prompt"

    # ==================== PUBLIC API ====================

    async def process_rag_query(
        self,
        user_query: str,
        user_id: str,
        profile_id: str,
        chat_history: list,
        context_summary: list = None,
        k: int = 5,
        attach_context_summary: bool = False,
        platform: str = "chatGPT"
    ) -> dict:
        """
        Process a RAG query using the agentic workflow

        Args:
            user_query: The user's input query
            user_id: User identifier
            profile_id: Profile identifier
            chat_history: Conversation history
            context_summary: Optional context summary (list of strings)
            k: Number of contexts to retrieve
            attach_context_summary: Whether to attach context summary to final prompt
            platform: Target platform (chatGPT, perplexity, gemini)

        Returns:
            dict: Contains optimized_prompt, context, sources, and metadata
        """
        print("[AGENTIC_RAG] Starting agentic RAG workflow")

        # Convert context_summary list to string for internal processing
        context_summary_str = ""
        if context_summary:
            if isinstance(context_summary, list):
                context_summary_str = " ".join(context_summary)
            else:
                context_summary_str = str(context_summary)

        # Initialize state
        initial_state = {
            "user_query": user_query,
            "user_id": user_id,
            "profile_id": profile_id,
            "chat_history": chat_history or [],
            "context_summary": context_summary_str,
            "k": k,
            "attach_context_summary": attach_context_summary,
            "platform": platform
        }

        # Execute the graph (use ainvoke for async nodes)
        final_state = await self.graph.ainvoke(initial_state)

        # Build response
        is_pluto = final_state.get("is_pluto_query", False)
        
        result = {
            "query": user_query,
            "optimized_prompt": final_state.get("optimized_prompt", user_query),
            "context": final_state.get("context", ""),
            "sources": final_state.get("sources", []),
            "total_contexts_found": len(final_state.get("relevant_docs", [])),
            "userId": user_id,
            "profileId": profile_id,
            "chat_history_considered": len(chat_history) > 0,
            "tokens_used": final_state.get("total_tokens_used", {}),
            "workflow_metadata": {
                "is_pluto_query": is_pluto,
                "query_type": final_state.get("query_type", "pluto" if is_pluto else "unknown"),
                "language": final_state.get("language", "English"),
                "query_expanded": bool(final_state.get("enhanced_query")),
                "separated_query": final_state.get("separated_query", user_query),
                "separated_data": final_state.get("separated_data", "None"),
                "errors": final_state.get("errors", [])
            }
        }

        if is_pluto:
            print(f"[AGENTIC_RAG] @pluto workflow completed. Contexts: {len(final_state.get('relevant_docs', []))}")
        else:
            print(f"[AGENTIC_RAG] Workflow completed. Query type: {final_state.get('query_type')}, Contexts: {len(final_state.get('relevant_docs', []))}")

        return result
