"""
Agentic Query Service using LangGraph
This service implements a state machine-based query processing system that dynamically handles
context search, tool calling (web search, URL extraction), and response generation.
"""

from typing import TypedDict, Annotated, Sequence
from typing_extensions import TypedDict
import operator
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage

from app.services.base_service import BaseService
from app.services.vector_service import VectorService
from app.services.llm_factory import llm_factory
from app.models.schemas import QueryRequest
from app.utils.chat_history_utils import optimize_chat_history


class AgenticQueryState(TypedDict):
    """State schema for the agentic query workflow"""
    # Input fields
    query_request: QueryRequest
    user_query: str
    user_id: str
    profile_id: str
    enable_web_search: bool
    enable_url_extraction: bool
    chat_history: list
    k: int
    model: str  # Selected model identifier (gemini or bedrock model key)

    # Intermediate fields
    chat_history_text: str
    relevant_docs: list
    context: str
    vague_query_processing: dict
    
    # System prompt and messages
    system_prompt: str
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # Tool execution tracking
    web_search_performed: bool
    url_content_extracted: bool
    web_search_queries: list
    extracted_urls: list
    available_tools: list
    
    # Output fields
    final_answer: str
    sources: list
    
    # Token tracking
    total_tokens_used: dict
    
    # Error tracking
    errors: list


class AgenticQueryService(BaseService):
    """
    Agentic Query Service that uses LangGraph to create a dynamic query processing pipeline.

    The workflow:
    1. Initialize → Set up default state
    2. Optimize Chat History → Reduce token usage
    3. Perform Context Search → Vector search for relevant documents
    4. Create System Prompt → Build prompt with context and tool policies
    5. Bind Tools → Conditionally bind web search and URL extraction tools
    6. Invoke LLM → Call LLM with messages
    7. Process Tool Calls → Execute tools if LLM requested them (loops back to Invoke LLM)
    8. Finalize Response → Extract answer and build sources
    """

    def __init__(self, context_service):
        """
        Initialize the AgenticQueryService
        
        Args:
            context_service: Reference to ContextService for accessing _perform_context_search
        """
        super().__init__()
        self.context_service = context_service
        self.vector_service = VectorService()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine for agentic query processing"""
        workflow = StateGraph(AgenticQueryState)
        
        # Add nodes
        workflow.add_node("initialize", self._initialize_query_node)
        workflow.add_node("optimize_chat_history", self._optimize_chat_history_query_node)
        workflow.add_node("perform_context_search", self._perform_context_search_node)
        workflow.add_node("create_system_prompt", self._create_system_prompt_node)
        workflow.add_node("bind_tools", self._bind_tools_node)
        workflow.add_node("invoke_llm", self._invoke_llm_node)
        workflow.add_node("process_tool_calls", self._process_tool_calls_node)
        workflow.add_node("finalize_response", self._finalize_response_node)
        
        # Define edges (workflow)
        workflow.set_entry_point("initialize")
        workflow.add_edge("initialize", "optimize_chat_history")
        workflow.add_edge("optimize_chat_history", "perform_context_search")
        workflow.add_edge("perform_context_search", "create_system_prompt")
        workflow.add_edge("create_system_prompt", "bind_tools")
        workflow.add_edge("bind_tools", "invoke_llm")
        
        # Conditional routing after LLM invocation
        workflow.add_conditional_edges(
            "invoke_llm",
            self._route_after_llm_invoke,
            {
                "process_tools": "process_tool_calls",
                "finalize": "finalize_response"
            }
        )
        
        # After processing tools, invoke LLM again
        workflow.add_edge("process_tool_calls", "invoke_llm")
        workflow.add_edge("finalize_response", END)
        
        return workflow.compile()

    # ==================== NODE IMPLEMENTATIONS ====================

    def _initialize_query_node(self, state: AgenticQueryState) -> dict:
        """Initialize the state with default values"""
        print("[AGENTIC_QUERY] Initializing workflow")
        return {
            "messages": [],
            "errors": [],
            "total_tokens_used": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            },
            "web_search_performed": False,
            "url_content_extracted": False,
            "web_search_queries": [],
            "extracted_urls": [],
            "available_tools": [],
            "relevant_docs": [],
            "context": "",
            "sources": [],
            "vague_query_processing": {},
            "chat_history_text": "",
            "final_answer": ""
        }

    async def _optimize_chat_history_query_node(self, state: AgenticQueryState) -> dict:
        """Optimize chat history to reduce token usage"""
        print("[AGENTIC_QUERY] Optimizing chat history")
        
        try:
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

    async def _perform_context_search_node(self, state: AgenticQueryState) -> dict:
        """Perform context search using the ContextService's _perform_context_search method"""
        print("[AGENTIC_QUERY] Performing context search")
        
        try:
            search_results = await self.context_service._perform_context_search(
                state["query_request"],
                state["chat_history_text"],
                state["total_tokens_used"]
            )
            
            return {
                "relevant_docs": search_results["relevant_docs"],
                "context": search_results["context"],
                "total_tokens_used": search_results["total_tokens_used"],
                "vague_query_processing": search_results["vague_query_processing"]
            }
        
        except Exception as e:
            print(f"[ERROR] Context search failed: {e}")
            state["errors"].append(f"Context search error: {str(e)}")
            return {
                "relevant_docs": [],
                "context": "",
                "vague_query_processing": {}
            }

    def _create_system_prompt_node(self, state: AgenticQueryState) -> dict:
        """Create the system prompt for the LLM"""
        print("[AGENTIC_QUERY] Creating system prompt")
        
        chat_history_text = state.get("chat_history_text", "")
        context = state.get("context", "")
        enable_web_search = state.get("enable_web_search", False)
        enable_url_extraction = state.get("enable_url_extraction", False)
        
        system_prompt = f"""You are Pluto - Plurality's Ontology Agent helping users with their questions based on their personal knowledge base and conversation history. 
        Provide comprehensive, detailed, and well-structured responses.

        Previous Conversation in latest first order:
        {chat_history_text}

        Relevant Context from Knowledge Base:
        {context}


        TOOL USAGE POLICY:
        - Web Search Tool: {"ENABLED - You can use web_search tool to find current information" if enable_web_search else "DISABLED - You cannot use web_search. If you think web search would help, ask the user to enable web search."}
        - URL Extraction Tool: {"ENABLED - You can use extract_url_content tool for URLs in messages" if enable_url_extraction else "DISABLED - You cannot use extract_url_content. If you think URL extraction would help, ask the user to enable URL extraction."}

        Instructions:
        1. Consider the conversation history to understand the context and any follow-up questions
        2. Use the relevant context from the knowledge base to provide accurate information
        3. If this is a follow-up question, reference previous parts of the conversation naturally
        4. "ONLY use the web_search tool if web search is ENABLED above"
        5. "ONLY use the extract_url_content tool if URL extraction is ENABLED above"
        6. If you think a disabled tool would be helpful, politely suggest the user enable it
        7. When using enabled tools, clearly indicate that the information comes from current web sources or specific websites
        8. Maintain a conversational tone that acknowledges the ongoing discussion
        9. Provide detailed, comprehensive responses with explanations, examples, and context where relevant
        10. Structure your responses with clear sections, bullet points, or numbered lists when appropriate

        IMPORTANT: Never call tools that are marked as DISABLED above. Instead, suggest enabling them if they would be helpful."""
        
        return {"system_prompt": system_prompt}

    def _bind_tools_node(self, state: AgenticQueryState) -> dict:
        """Bind tools based on enabled filters"""
        print("[AGENTIC_QUERY] Binding tools")
        
        available_tools = []
        
        if state.get("enable_web_search", False):
            available_tools.append(self.context_service.web_search_tool)
            print(f"[TOOL_BINDING] Web search tool enabled")
        
        if state.get("enable_url_extraction", False):
            available_tools.append(self.context_service.url_content_tool)
            print(f"[TOOL_BINDING] URL extraction tool enabled")
        
        if not available_tools:
            print(f"[TOOL_BINDING] No tools enabled")
        
        return {"available_tools": available_tools}

    def _invoke_llm_node(self, state: AgenticQueryState) -> dict:
        """Invoke the LLM with the current messages"""
        selected_model = state.get("model", "gemini")
        print(f"[AGENTIC_QUERY] Invoking LLM with model: {selected_model}")

        try:
            messages = state.get("messages", [])

            # For Gemini with tools, ensure proper message sequence
            # Gemini requires: HumanMessage -> AIMessage -> ToolMessage -> AIMessage pattern
            if len(messages) == 0:
                # First invocation - create initial user message with system prompt
                combined_prompt = f"""{state["system_prompt"]}

---

Current Question: {state['user_query']}
Please provide a comprehensive, detailed response that thoroughly addresses the question. Include explanations, context, and relevant details to make your answer as helpful and complete as possible."""

                messages = [
                    HumanMessage(content=combined_prompt)
                ]
            else:
                # Subsequent invocations after tool calls
                # Ensure we have HumanMessage at the start for Gemini
                # Pattern should be: [HumanMessage, AIMessage(tool_calls), ToolMessage, ToolMessage, ...]
                if messages and not isinstance(messages[0], HumanMessage):
                    # Prepend the original user message if it's missing
                    combined_prompt = f"""{state["system_prompt"]}

---

Current Question: {state['user_query']}
Please provide a comprehensive, detailed response that thoroughly addresses the question. Include explanations, context, and relevant details to make your answer as helpful and complete as possible."""

                    messages = [HumanMessage(content=combined_prompt)] + list(messages)

                # Add a follow-up instruction after tool results for prompt-based models
                # This helps models like GPT-OSS understand they should synthesize an answer
                if any(isinstance(m, ToolMessage) for m in messages):
                    messages = list(messages) + [HumanMessage(content="Based on the tool results above, please provide a comprehensive answer to my original question.")]

            # Get LLM based on selected model using the factory
            base_llm = llm_factory.get_llm(selected_model)

            # Bind tools if available
            available_tools = state.get("available_tools", [])
            if available_tools:
                llm_to_use = base_llm.bind_tools(available_tools)
                print(f"[TOOL_BINDING] LLM bound with {len(available_tools)} tools (model: {selected_model})")
            else:
                llm_to_use = base_llm
                print(f"[TOOL_BINDING] LLM used without tools (model: {selected_model})")

            # Invoke LLM
            response = llm_to_use.invoke(messages)

            # Track token usage
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = response.usage_metadata
                input_tokens = usage.get('input_tokens', 0)
                output_tokens = usage.get('output_tokens', 0)
                state["total_tokens_used"]["input_tokens"] += input_tokens
                state["total_tokens_used"]["output_tokens"] += output_tokens
                state["total_tokens_used"]["total_tokens"] += input_tokens + output_tokens
            
            # Return the response and updated messages
            return {
                "messages": [response],
                "total_tokens_used": state["total_tokens_used"]
            }
        
        except Exception as e:
            print(f"[ERROR] LLM invocation failed: {e}")
            state["errors"].append(f"LLM invocation error: {str(e)}")
            # Return a dummy response to prevent workflow failure
            return {
                "messages": [AIMessage(content=f"Error: {str(e)}")],
            }

    def _process_tool_calls_node(self, state: AgenticQueryState) -> dict:
        """Process tool calls from the LLM response"""
        print("[AGENTIC_QUERY] Processing tool calls")
        
        messages = state.get("messages", [])
        if not messages:
            return {}
        
        response = messages[-1]
        tool_messages = []
        
        try:
            for tool_call in response.tool_calls:
                if tool_call["name"] == "web_search":
                    query = tool_call["args"]["query"]
                    state["web_search_queries"].append(query)
                    state["web_search_performed"] = True
                    print("[WEB_SEARCH] Performing web search")

                    # Execute the tool
                    tool_result = self.context_service.web_search_tool.invoke(tool_call["args"])
                    
                    # Add tool message
                    tool_message = ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call["id"],
                        name=tool_call["name"]
                    )
                    tool_messages.append(tool_message)
                
                elif tool_call["name"] == "extract_url_content":
                    url = tool_call["args"]["url"]
                    state["extracted_urls"].append(url)
                    state["url_content_extracted"] = True
                    print("[URL_EXTRACT] Extracting URL content")

                    # Execute the tool
                    tool_result = self.context_service.url_content_tool.invoke(tool_call["args"])
                    
                    # Add tool message
                    tool_message = ToolMessage(
                        content=tool_result,
                        tool_call_id=tool_call["id"],
                        name=tool_call["name"]
                    )
                    tool_messages.append(tool_message)
            
            return {
                "messages": tool_messages,
                "web_search_performed": state["web_search_performed"],
                "url_content_extracted": state["url_content_extracted"],
                "web_search_queries": state["web_search_queries"],
                "extracted_urls": state["extracted_urls"]
            }
        
        except Exception as e:
            print(f"[ERROR] Tool processing failed: {e}")
            state["errors"].append(f"Tool processing error: {str(e)}")
            return {}

    def _finalize_response_node(self, state: AgenticQueryState) -> dict:
        """Finalize the response by extracting the answer and building sources"""
        print("[AGENTIC_QUERY] Finalizing response")

        messages = state.get("messages", [])
        if not messages:
            return {"final_answer": "No response generated"}

        # Get the last AI message
        response = messages[-1]
        final_answer = self._extract_text_from_response(response)
        
        # Build sources from relevant docs
        sources = []
        for doc in state.get("relevant_docs", []):
            content_type = doc['metadata'].get("contentType", "unknown")
            source_info = {
                "title": doc['metadata'].get("title", "Untitled"),
                "profileId": doc['metadata'].get("profileId", "Unknown"),
                "contentType": content_type,
                "createdAt": doc['metadata'].get("createdAt", "Unknown")
            }
            
            if content_type == "file":
                source_info.update({
                    "fileName": doc['metadata'].get("fileName", "Unknown"),
                    "fileType": doc['metadata'].get("fileType", "Unknown"),
                    "fileId": doc['metadata'].get("fileId", "Unknown")
                })
            else:
                source_info["contextId"] = doc['metadata'].get("contextId", "Unknown")
            
            sources.append(source_info)
        
        # Add web search to sources if performed
        if state.get("web_search_performed", False):
            sources.append({
                "title": "Web Search Results",
                "contentType": "web_search",
                "searchQueries": state.get("web_search_queries", []),
                "searchPerformed": True,
                "dynamicToolCall": True
            })
        
        # Add URL extraction to sources if performed
        if state.get("url_content_extracted", False):
            sources.append({
                "title": "URL Content Extraction",
                "contentType": "url_extraction",
                "extractedUrls": state.get("extracted_urls", []),
                "extractionPerformed": True,
                "dynamicToolCall": True
            })
        
        return {
            "final_answer": final_answer,
            "sources": sources
        }

    # ==================== HELPER FUNCTIONS ====================

    def _extract_text_from_response(self, response) -> str:
        """
        Extract text content from Gemini 3 response which may include thinking blocks.
        Gemini 3 returns responses with 'thinking' and 'text' fields when include_thoughts=True.
        """
        if not hasattr(response, 'content'):
            return str(response)

        content = response.content

        # If content is a string, return it directly
        if isinstance(content, str):
            return content

        # If content is a list (Gemini 3 format with thinking/text blocks)
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict):
                    # Extract only the 'text' field, skip 'thinking'
                    if part.get('type') == 'text' and 'text' in part:
                        text_parts.append(part['text'])
                elif isinstance(part, str):
                    text_parts.append(part)
            return '\n'.join(text_parts) if text_parts else str(content)

        # Fallback
        return str(content)

    # ==================== ROUTING FUNCTIONS ====================

    def _route_after_llm_invoke(self, state: AgenticQueryState) -> str:
        """Decide whether to process tool calls or finalize response"""
        messages = state.get("messages", [])
        if not messages:
            return "finalize"
        
        response = messages[-1]
        
        # Check if there are tool calls
        if hasattr(response, 'tool_calls') and response.tool_calls:
            print(f"[AGENTIC_QUERY] Routing to tool processing ({len(response.tool_calls)} calls)")
            return "process_tools"
        else:
            print("[AGENTIC_QUERY] Routing to finalization")
            return "finalize"

    # ==================== PUBLIC API ====================

    async def process_query(
        self,
        query_request: QueryRequest,
    ) -> dict:
        """
        Process a query using the agentic workflow

        Args:
            query_request: QueryRequest object with all query parameters

        Returns:
            dict: Contains answer, sources, token usage, and workflow metadata
        """
        print("[AGENTIC_QUERY] Starting agentic query workflow")

        # Initialize state
        initial_state = {
            "query_request": query_request,
            "user_query": query_request.query,
            "user_id": query_request.userId,
            "profile_id": query_request.profileId,
            "enable_web_search": query_request.enableWebSearch,
            "enable_url_extraction": query_request.enableUrlExtraction,
            "chat_history": query_request.chatHistory or [],
            "k": query_request.k,
            "model": query_request.model or "gemini"  # Selected model (defaults to Gemini)
        }

        # Execute the graph (use ainvoke for async nodes)
        final_state = await self.graph.ainvoke(initial_state)

        # Extract results
        final_answer = final_state.get("final_answer", "")
        sources = final_state.get("sources", [])
        relevant_docs = final_state.get("relevant_docs", [])
        total_tokens_used = final_state.get("total_tokens_used", {})
        vague_query_processing = final_state.get("vague_query_processing", {})
        web_search_performed = final_state.get("web_search_performed", False)
        url_content_extracted = final_state.get("url_content_extracted", False)
        web_search_queries = final_state.get("web_search_queries", [])
        extracted_urls = final_state.get("extracted_urls", [])

        print(f"[AGENTIC_QUERY] Workflow completed. Found {len(relevant_docs)} contexts")
        if web_search_performed:
            print(f"[WEB_SEARCH] Total searches: {len(web_search_queries)}")
        if url_content_extracted:
            print(f"[URL_EXTRACT] Total extractions: {len(extracted_urls)}")

        # Build response
        return {
            "answer": final_answer,
            "sources": sources,
            "total_contexts_found": len(relevant_docs),
            "userId": query_request.userId,
            "chat_history_considered": len(query_request.chatHistory) > 0,
            "web_search_performed": web_search_performed,
            "url_content_extracted": url_content_extracted,
            "web_search_queries": web_search_queries,
            "extracted_urls": extracted_urls,
            # Token usage tracking
            "tokens_used": total_tokens_used,
            # New fields for filter tracking
            "explicit_filters_used": {
                "webSearch": query_request.enableWebSearch,
                "urlExtraction": query_request.enableUrlExtraction
            },
            "dynamic_tool_calls": {
                "webSearchPerformed": web_search_performed,
                "urlExtractionPerformed": url_content_extracted,
                "webSearchQueries": web_search_queries,
                "extractedUrls": extracted_urls
            },
            # Vague query processing fields
            "vague_query_processing": vague_query_processing,
            # Workflow metadata
            "workflow_metadata": {
                "agentic": True,
                "errors": final_state.get("errors", [])
            }
        }

