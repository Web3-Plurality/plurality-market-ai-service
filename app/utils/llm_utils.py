"""
LLM-based utility functions for text analysis and generation
These functions require an LLM instance to be passed as a parameter
"""

from typing import Any
from langchain_core.messages import HumanMessage
from app.utils.text_utils import parse_llm_response


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
