"""
Text processing utility functions for chat history, parsing, and formatting
"""

from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter


def normalize_chat_history(chat_history: List) -> List:
    """Normalize chat history to standard format"""
    normalized_messages = []
    for message in chat_history:
        if hasattr(message, 'role') or (isinstance(message, dict) and 'role' in message):
            role = message.role if hasattr(message, 'role') else message.get('role', 'unknown')
            content = message.content if hasattr(message, 'content') else message.get('content', '')
            normalized_messages.append({"role": role, "content": content})
        
        # Check if it's the paired format with 'user' and 'assistant' keys
        elif isinstance(message, dict):
            # Add user message if present
            if 'user' in message and message['user']:
                normalized_messages.append({"role": "user", "content": message['user']})
            
            # Add assistant message if present
            if 'assistant' in message and message['assistant']:
                normalized_messages.append({"role": "assistant", "content": message['assistant']})
    return normalized_messages


def estimate_tokens(text: str) -> int:
    """Estimate token count (approximation: 1 token ≈ 4 characters for English)"""
    return len(text) // 4


def calculate_metadata_bytes(metadata: dict, exclude_keys: list = None) -> int:
    """
    Calculate the byte size of metadata when encoded as UTF-8.

    Args:
        metadata: Dictionary containing metadata fields
        exclude_keys: List of keys to exclude from calculation (e.g., ['content'])

    Returns:
        Total bytes used by metadata
    """
    exclude_keys = exclude_keys or []
    total_bytes = 0

    for key, value in metadata.items():
        if key in exclude_keys:
            continue

        # Convert value to string and calculate UTF-8 bytes
        if value is not None:
            value_str = str(value)
            total_bytes += len(value_str.encode('utf-8'))
            # Add bytes for the key itself
            total_bytes += len(key.encode('utf-8'))

    # Add overhead for JSON structure (colons, quotes, commas, braces)
    # Rough estimate: 10 bytes per field for JSON formatting
    total_bytes += len(metadata) * 10

    return total_bytes


def chunk_content_by_bytes(content: str, metadata: dict, max_total_bytes: int = 2048, safety_buffer: int = 200) -> list:
    """
    Chunk content based on byte limits while respecting metadata size.

    Args:
        content: The text content to chunk
        metadata: Base metadata that will be attached to each chunk
        max_total_bytes: Maximum bytes allowed for metadata (AWS S3 Vectors limit)
        safety_buffer: Safety buffer in bytes to account for encoding variations

    Returns:
        List of content chunks that will fit within byte limits when combined with metadata
    """
    # Calculate base metadata size (excluding 'content' field)
    base_metadata_bytes = calculate_metadata_bytes(metadata, exclude_keys=['content'])

    # Calculate available bytes for content
    available_bytes = max_total_bytes - base_metadata_bytes - safety_buffer

    print(f"[BYTE_CHUNKING] Base metadata: {base_metadata_bytes} bytes, Available for content: {available_bytes} bytes")

    if available_bytes <= 0:
        raise ValueError(f"Metadata too large! Base metadata uses {base_metadata_bytes} bytes, leaving no room for content. Maximum allowed: {max_total_bytes} bytes")

    # Measure the actual byte-to-character ratio of THIS content
    content_bytes = len(content.encode('utf-8'))
    content_chars = len(content)
    bytes_per_char = content_bytes / content_chars if content_chars > 0 else 1.5

    print(f"[BYTE_CHUNKING] Content analysis: {content_chars} chars = {content_bytes} bytes, ratio: {bytes_per_char:.2f} bytes/char")

    # Calculate chunk size in characters based on actual content ratio
    # Use available_bytes directly since we're using byte-based length_function
    chunk_size_bytes = available_bytes

    # Create a temporary splitter with byte-based chunk size
    byte_aware_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size_bytes,
        chunk_overlap=min(200, chunk_size_bytes // 10),  # 10% overlap or 200 bytes, whichever is smaller
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=lambda text: len(text.encode('utf-8'))  # Use byte length - this is the key!
    )

    chunks = byte_aware_splitter.split_text(content)

    # Verify each chunk fits within byte limit
    verified_chunks = []
    for i, chunk in enumerate(chunks):
        chunk_bytes = len(chunk.encode('utf-8'))
        total_with_metadata = base_metadata_bytes + chunk_bytes

        if total_with_metadata > max_total_bytes:
            print(f"[WARNING] Chunk {i} still too large ({total_with_metadata} bytes), further splitting...")
            # If still too large, force split by bytes
            max_chunk_bytes = available_bytes
            while len(chunk.encode('utf-8')) > max_chunk_bytes:
                # Binary search for the right substring length
                safe_length = len(chunk) * max_chunk_bytes // len(chunk.encode('utf-8'))
                sub_chunk = chunk[:safe_length]
                # Find last sentence boundary
                last_period = sub_chunk.rfind('. ')
                last_newline = sub_chunk.rfind('\n')
                last_space = sub_chunk.rfind(' ')

                split_point = max(last_period, last_newline, last_space)
                if split_point > 0:
                    verified_chunks.append(chunk[:split_point])
                    chunk = chunk[split_point:].strip()
                else:
                    # Force split if no boundary found
                    verified_chunks.append(sub_chunk)
                    chunk = chunk[safe_length:].strip()

            if chunk:
                verified_chunks.append(chunk)
        else:
            verified_chunks.append(chunk)
            print(f"[BYTE_CHUNKING] Chunk {i}: {chunk_bytes} bytes (total with metadata: {total_with_metadata} bytes)")

    return verified_chunks


def parse_llm_response(response_text: str) -> dict:
    """Parse structured LLM response into sections"""
    sections = {
        "title": "",
        "insights": "",
        "description": ""
    }

    lines = response_text.split('\n')
    current_section = None
    current_content = []

    for line in lines:
        line = line.strip()

        if line.startswith('TITLE:'):
            sections["title"] = line.replace('TITLE:', '').strip()
            current_section = None
        elif line.startswith('INSIGHTS:'):
            current_section = "insights"
            current_content = []
            # Check if there's content on the same line as INSIGHTS:
            inline_content = line.replace('INSIGHTS:', '').strip()
            if inline_content:
                current_content.append(inline_content)
        elif line.startswith('DESCRIPTION:'):
            current_section = "description"
            current_content = []
            # Check if there's content on the same line as DESCRIPTION:
            inline_content = line.replace('DESCRIPTION:', '').strip()
            if inline_content:
                current_content.append(inline_content)
        elif current_section and line:
            if current_section == "description":
                current_content.append(line)
            elif current_section in ["insights"]:
                current_content.append(line)

            # Update the section content
            if current_content:
                sections[current_section] = '\n'.join(current_content)

    # Ensure final content is captured (in case loop ends without updating)
    if current_section and current_content:
        sections[current_section] = '\n'.join(current_content)

    # Clean up title
    if sections["title"]:
        sections["title"] = sections["title"].strip('"\'').strip()
        if len(sections["title"]) > 60:
            sections["title"] = sections["title"][:57] + "..."

    return sections


