"""
LLM-based utility functions for text analysis and generation
These functions require an LLM instance to be passed as a parameter
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from app.utils.text_utils import parse_llm_response, parse_query_data_response, trim_to_complete_sentences


async def extract_title_and_description(llm: Any, content: str, filename: str = None) -> dict:
    """Extract a meaningful title and bullet point description from content using LLM"""
    # Use first 1000 characters for title and description extraction
    content_preview = content[:1000] if len(content) > 1000 else content
    
    title_and_desc_prompt = f"""
    Based on the following document content, generate:
    1. A concise and descriptive title (maximum 2 to 3 words) that captures the main topic
    2. A bullet point description (3-5 bullet points, each 1-2 lines) summarizing the key points
    
    {f"Filename: {filename}" if filename else ""}
    Content: {content_preview}
    
    Please respond in this exact format:
    TITLE: [Your title here]
    DESCRIPTION:
    • [First key point]
    • [Second key point]
    • [Third key point]
    """
    
    try:
        # Use HumanMessage for chat model
        llm_response = await llm.ainvoke([HumanMessage(content=title_and_desc_prompt)])
        response_text = llm_response.content.strip()
        
        # Parse the response to extract title and description
        lines = response_text.split('\n')
        extracted_title = ""
        extracted_description = ""
        
        # Find title
        for line in lines:
            if line.strip().startswith('TITLE:'):
                extracted_title = line.replace('TITLE:', '').strip()
                break
        
        # Find description (collect all bullet points)
        description_started = False
        description_lines = []
        for line in lines:
            if line.strip() == 'DESCRIPTION:':
                description_started = True
                continue
            if description_started and line.strip().startswith('•'):
                description_lines.append(line.strip())
        
        extracted_description = '\n'.join(description_lines) if description_lines else ""
        
        # Clean up the title
        extracted_title = extracted_title.strip('"\'').strip()
        
        # Ensure title is not too long
        if len(extracted_title) > 60:
            extracted_title = extracted_title[:57] + "..."
            
        # Fallback handling
        if not extracted_title or len(extracted_title) < 3:
            extracted_title = filename.split('.')[0] if filename else "untitled"
            
        if not extracted_description:
            extracted_description = "• Key content extracted from document\n• Available for search and retrieval"
            
        return {
            "title": extracted_title,
            "description": extracted_description
        }
            
    except Exception as e:
        print(f"[WARNING] Failed to extract title and description: {e}")
        fallback_title = filename.split('.')[0] if filename else "untitled"
        fallback_description = "• Content extracted from document\n• Available for search and retrieval"
        
        return {
            "title": fallback_title,
            "description": fallback_description
        }


async def extract_insights_and_summary(llm: Any, chat_text: str) -> dict:
    """Extract insights, user information, and summary from chat history using LLM"""
    
    insights_prompt = f"""
    Analyze the following chat conversation and extract:
    
    1. A concise title (2 to 3 words max) that captures the main topic or theme of the conversation
    2. Specific user insights including:
       - Key information user provided in the text
       - Facts mentioned in the text
       - User preferences, interests, and behaviors mentioned
       - Personal information shared (goals, challenges, background)
       - Learning patterns or knowledge gaps identified
       - Communication style and personality traits observed
    3. Description summarizing the key aspects of this conversation
    
    Chat History:
    {chat_text}
    
    IMPORTANT: Use only plain text formatting. Do not use markdown, asterisks (*), double asterisks (**), or any other formatting symbols. Use simple line breaks and dashes for lists.
    
    Please respond in this exact format:
    TITLE: [Your title here - use plain text only, no formatting symbols]
    
    
    INSIGHTS:
    [Detailed user insights and information extracted from the chat - use plain text only, no formatting symbols]
    
    DESCRIPTION:
    [Description summarizing the key aspects of this conversation - use plain text only, no formatting symbols]
    """
    
    try:
        # Use HumanMessage for chat model
        llm_response = await llm.ainvoke([HumanMessage(content=insights_prompt)])
        response_text = llm_response.content.strip()

        # Parse the response to extract different sections
        sections = parse_llm_response(response_text)
        
        return {
            "title": sections.get("title", "Chat Conversation"),
            "insights": sections.get("insights", "User insights not available"),
            "description": sections.get("description", "• Chat conversation processed\n• User interaction data captured")
        }
        
    except Exception as e:
        print(f"[ERROR] LLM insights extraction failed, using fallback: {e}")
        return {
            "title": "Chat Conversation",
            "insights": "User interaction patterns and preferences captured from conversation",
            "description": "• Chat conversation processed\n• User interaction data captured\n• Available for context retrieval"
        }


async def separate_query_and_data(llm: Any, user_input: str, total_tokens_used: dict) -> dict:
    """
    Separates user questions/queries from data they're providing using LLM analysis.
    This helps distinguish between what the user is asking and what information they're sharing.
    
    Args:
        llm: LLM instance to use for analysis
        user_input (str): The raw user input that may contain both questions and data
        total_tokens_used (dict): Token usage tracking dictionary (updated in-place)
        
    Returns:
        dict: Contains separated 'query', 'data', 'analysis', and 'separation_confidence'
    """
    system_message = SystemMessage(content="""You are an expert text analysis assistant specialized in parsing and separating user inputs.

                    Your expertise:
                    - Distinguishing between questions/requests and provided information/data
                    - Identifying code blocks, data structures, and contextual information
                    - Understanding natural language patterns and separators

                    Your task:
                    - Separate user input into QUERY (what they're asking) and DATA (what they're providing)
                    - Extract code blocks, examples, or data from queries and move them to DATA section
                    - Use punctuation, newlines, and formatting as separation cues
                    - Identify DATA only if clearly separate information is provided
                    - When in doubt, keep everything as QUERY

                    Output requirements:
                    - Always provide a QUERY (the main question or request)
                    - Set DATA to "None" if no data is provided
                    - Enclose DATA in triple backticks if present
                    - Be precise and maintain original meaning""")

    human_message = HumanMessage(content=f"""Analyze and separate the following user input:

                    User Input:
                    {user_input}

                    Separate into:
                    1. QUERY: The question, request, or instruction
                    2. DATA: Any information, code, examples, or data provided

                    Rules:
                    - Move any code blocks or inline code from QUERY to DATA
                    - Use `:`, newlines, or formatting as separation cues
                    - If no data present, set DATA to "None"
                    - If only data (no query), extract the implicit query
                    - Don't force extraction - when uncertain, leave in QUERY

                    Response format:
                    QUERY: [the question or request]

                    DATA: [the provided information or "None"]""")

    try:
        llm_response = await llm.ainvoke([system_message, human_message])            
        # Track token usage
        if hasattr(llm_response, 'usage_metadata') and llm_response.usage_metadata:
            usage = llm_response.usage_metadata
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            total_tokens_used["input_tokens"] += input_tokens
            total_tokens_used["output_tokens"] += output_tokens
            total_tokens_used["total_tokens"] += input_tokens + output_tokens
        
        response_text = llm_response.content.strip()

        # Parse the structured response
        result = parse_query_data_response(response_text)

        # Add original input for reference
        result["original_input"] = user_input

        result["total_tokens_used"] = total_tokens_used
        print(f"[QUERY_DATA_SEPARATION] Processed input Data")
        return result
        
    except Exception as e:
        print(f"[ERROR] Failed to separate query and data: {e}")
        # Fallback: treat entire input as query if separation fails
        return {
            "original_input": user_input,
            "query": user_input,
            "data": "None",
            "total_tokens_used": total_tokens_used,
            "error": str(e)
        }


async def check_context_relevance(llm: Any, query: str, context: str) -> str:
    """
    Finds out the intention behind the query using LLM analysis.
    This helps distinguish between what the user is asking and key inputs.
    """
    
    relevance_prompt = f"""
    You are an expert at analyzing user query to find out its relevance with provided context.
    Analyze the following user query and the context provided and find out if both are relevant.
    
    User Query: {query}

    Context: {context if context else "No specific context available"}
    
    Instructions:
    - If the 'User Query' is relevant to the 'Context', Grammar fix the 'Context' in above text so that it looks like a continued text. Do not add Title or Content of any kind of headings. Enclose the response text in triple backticks (i.e., ``` ... ```).
    - If the 'User Query' is NOT relevant to the 'Context', return ````No Relevant Context Found````
    """

    try:
        # Use LLM to separate query and data
        llm_response = await llm.ainvoke([HumanMessage(content=relevance_prompt)])
        relevant_context = llm_response.content.strip()
        print("relevant_context\n", relevant_context)
        return relevant_context
        
    except Exception as e:
        print(f"[ERROR] Failed to check context relevance: {e}")
        # Fallback: treat entire input as query if separation fails
        return {
            "query": query,
            "context": context,
            "error": str(e)
        }


async def check_prompt_language(llm: Any, query: str, total_tokens_used: dict) -> dict:
    """
    Detect the language of the user's query, including transliterated/romanized text.
    
    This function identifies both native scripts and romanized forms where one language
    is written using Latin/Roman alphabet (common in South Asian and East Asian languages).
    
    Args:
        llm: LLM instance to use for detection
        query: The user's input query
        total_tokens_used: Token usage tracking dictionary (updated in-place)
        
    Returns:
        dict: Contains detected language name and total tokens used. Format:
            - language: Detected language name. Format:
                - Native script: "English", "Spanish", "Arabic", "Hindi", "Chinese", etc.
                - Romanized: "Roman Urdu", "Roman Hindi", "Roman Arabic", "Roman Chinese", etc.
            - total_tokens_used: Total tokens used for the language detection
    """
    
    # System message: Define the AI's role and persona
    system_message = SystemMessage(content="""You are a professional language detection specialist with expertise in linguistic analysis.
                            Your core competencies:
                            - Identifying languages from text samples with high accuracy
                            - Detecting transliterated/romanized text (when one language is written using Latin/Roman alphabet)
                            - Distinguishing between native scripts and romanized forms
                            - Understanding common romanization patterns across multiple language families

                            Your approach:
                            - Analyze vocabulary, grammar patterns, and script used
                            - Identify if Latin alphabet is being used to write a non-Latin language
                            - Provide clear, concise language identification

                            Common romanized languages you handle:
                            - South Asian: Roman Urdu, Roman Hindi, Roman Punjabi, Roman Bengali
                            - Middle Eastern: Roman Arabic, Roman Persian, Roman Turkish
                            - East Asian: Roman Chinese (Pinyin), Roman Japanese (Romaji), Roman Korean

                            Output format:
                            - Native script: Return language name only (e.g., "English", "Arabic", "Hindi")
                            - Romanized text: Return "Roman [Language]" (e.g., "Roman Urdu", "Roman Arabic")
                            - Default: Return "English" if uncertain""")
    
    # Human message: The actual task with user's query
    human_message = HumanMessage(content=f"""Analyze the following text and identify its language:
                                    Text to analyze:
                                    {query}

                                    Instructions:
                                    1. Determine the primary language used
                                    2. Check if it's written in native script or romanized (using Latin/Roman alphabet)
                                    3. For romanized text, identify the underlying language

                                    Return only the language name or "Roman [Language]" format. No explanations, just the result.""")

    try:
        prompt_language = {
            "language": "English",
            "total_tokens_used": total_tokens_used
        }
        # Use LLM to detect language with proper message structure
        llm_response = await llm.ainvoke([system_message, human_message])
        
        # Track token usage
        if hasattr(llm_response, 'usage_metadata') and llm_response.usage_metadata:
            usage = llm_response.usage_metadata
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            total_tokens_used["input_tokens"] += input_tokens
            total_tokens_used["output_tokens"] += output_tokens
            total_tokens_used["total_tokens"] += input_tokens + output_tokens
        
        prompt_language["language"] = llm_response.content.strip()
        prompt_language["total_tokens_used"] = total_tokens_used
        print(f"[LANGUAGE_DETECTION] Detected language: {prompt_language['language']}")
        
        return prompt_language
        
    except Exception as e:
        print(f"[ERROR] Language detection failed: {e}")
        # Fallback to English on error
        return {
            "language": "English",
            "total_tokens_used": total_tokens_used
        }


async def generate_optimized_llm_prompt(
    llm: Any,
    query: str,
    context: str,
    data: str,
    chat_text: str,
    language: str,
    total_tokens_used: dict,
    attachContextSummary: bool = False,
    platform: str = "chatGPT"
) -> str:
    """
    Generates an optimized prompt for the LLM based on the retrieved context and chat history.
    This helps the LLM focus on the most relevant information and context.
    """
    print("attachContextSummary", attachContextSummary)

    if data and len(data) > 20:
        data_info_msg = "The chat agent you are optimizing for has access to the extra data this query is about, so ask the chat agent to use the extra data"
    else:
        data_info_msg = "There is no extra data provided by the user"
    
    # By default, do not show context if chat history is present
    show_context = False
    
    meta_prompt = ""
    if  len(chat_text) == 0:
        # We may show context if conversation history is not available i.e. this is first message
        show_context = True 
        meta_prompt = f"""
        You are AI assistant optimizing the system prompt for a chat agent.
        Based on the following information, create an optimized system prompt that will help an AI assistant provide the best possible response:
        User's Query: {query}
        
        Retrieved Context: {context[:100000] if context else "No specific context available"}
        
        Conversation History: {chat_text if len(chat_text) > 0 else "No conversation history available"}
        
        IMPORTANT: { data_info_msg }
        IMPORTANT: Generate the optimized prompt in {language}

        Your task: Generate a clear, focused system prompt that:
        1. IMPORTANT: Defines the AI assistant's role appropriately for this specific query
        2. Analyze the user's query in the context of the provided summary and conversation history
        3. Try to understand what the user might be looking for or asking about
        4. If you can infer the user's intent, provide a more detailed and specific interpretation of their query
        5. Focus on extracting key concepts, topics, or areas the user might be interested in
        6. Do not make up information - only work with what's provided in the context
        7. Do not include any userId or profileId or any kind of id given to you in the system prompt
        8. Response should not contain markdown language for formatting. 
        - If you need to highlight or format something important (such as code snippets, raw data, commands, or key values), 
        - use triple backticks
         ```
         your-data-or-important-information
         ```
        - Do NOT use markdown headers, bullet points, or blockquotes outside the above guidance.


        
        Return ONLY the optimized system prompt, nothing else.
        """
    else:
        # Create a following prompt
        meta_prompt = f"""
        You are AI assistant optimizing the system prompt for a chat agent.
        Based on the following information, create an optimized system prompt that will help an AI assistant provide the best possible response:

        User's Original Query: {query}
        
        Retrieved Context: {context[:100000] if context else "No specific context available"}
        
        Conversation History: {chat_text if len(chat_text) > 0 else "No conversation history available"}
        
        IMPORTANT: The chat agent you are optimizing for already has access to the same conversation history provided above. 
        IMPORTANT: { data_info_msg }
        IMPORTANT: Generate the optimized prompt in {language}

        Your task: Generate a clear, focused system prompt that:
        1. First, analyze the relationship between the user's query and the conversation history:
        a) Complex query with relevant history: Query introduces new aspects but builds on previous discussion
        b) Completely different query: Query is unrelated to conversation history
        
        2. If the query is on a relevant history:
        - IMPORTANT: Define the AI assistant's role appropriately for this specific query
        - Analyze the user's query in the context of the provided summary and conversation history
        - Try to understand what the user might be looking for or asking about
        - Optimize the query based solely on its own merit and the retrieved context
        - The chat agent already knows the history context, so avoid repeating or referencing it unnecessarily
        - Always focus on the user query and prioritize the query more than the context and chat history.

        3. If the query is completely different and unrelated to conversation history:
        - IMPORTANT: Define the AI assistant's role appropriately for this specific query
        - Treat this as a fresh query and do NOT consider the conversation history in your optimization
        - Focus entirely on the new query and any relevant retrieved context
        - Optimize the query based solely on its own merit and the retrieved context
        - Do not reference or be influenced by irrelevant conversation history
        
        4. Do not make up information - only work with what's provided in the context
        5. Do not include any userId or profileId or any kind of id given to you in the system prompt
        6. Remember: The target chat agent has the same conversation history, so avoid redundant context repetition for simple queries
        7. Always focus on the user query and prioritize the query more than the context and chat history.
        8. Response should not contain markdown language for formatting. 
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
        - Any assumptions about the data provided by the user along with this query
        
        Return the clean system prompt text that can be directly used by the target chat agent.
        """
    
    # Invoke the LLM to generate the optimized prompt
    llm_response = await llm.ainvoke([HumanMessage(content=meta_prompt)])
    
    # Track token usage for the optimized prompt generation
    if hasattr(llm_response, 'usage_metadata') and llm_response.usage_metadata:
        usage = llm_response.usage_metadata
        input_tokens = usage.get('input_tokens', 0)
        output_tokens = usage.get('output_tokens', 0)
        total_tokens_used["input_tokens"] += input_tokens
        total_tokens_used["output_tokens"] += output_tokens
        total_tokens_used["total_tokens"] += input_tokens + output_tokens

    # Clean up the response and remove any unwanted analysis text
    optimized_prompt = llm_response.content.strip()

    print("query", query)
    print("data", data)
    print("context", context)
    if data and len(data) > 20:
        if platform == "perplexity" or platform == "gemini":
            optimized_prompt = (
            f"{optimized_prompt}"
            f"\n Here is the specific data: \n"
            f"{data.replace('```', '').strip()}"
        )
        else:
           optimized_prompt = (
            f"{optimized_prompt}"
            f"\n ```Here is the specific data:``` \n"
            f"```{data.replace('```', '').strip()}```"
        )


    if show_context and attachContextSummary and context and len(context) > 100:
        # Trim context to complete sentences (remove incomplete sentences from start and end)
        trimmed_context = trim_to_complete_sentences(context.replace('```', '').strip())

        if platform == "perplexity" or platform == "gemini":
            optimized_prompt = (
            f"{optimized_prompt}"
            f"\n Here is the specific context: \n"
            f"{trimmed_context}"
        )
        else:
            optimized_prompt = (
                f"{optimized_prompt}"
                f"\n ```Here is the specific context:``` \n"
                f"```{trimmed_context}```"
            )

        

    print(f"[OPTIMIZED_PROMPT] Generated optimized prompt based on context analysis")
    return optimized_prompt



