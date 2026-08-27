"""
File handling utility functions for document loading and processing
"""

import subprocess
from typing import Any
from fastapi import HTTPException
from langchain_community.document_loaders import (
    TextLoader, Docx2txtLoader, PyPDFLoader, UnstructuredMarkdownLoader, JSONLoader,
    UnstructuredPowerPointLoader, UnstructuredExcelLoader, CSVLoader,
    UnstructuredHTMLLoader, UnstructuredRTFLoader, UnstructuredODTLoader,
    UnstructuredEPubLoader, UnstructuredWordDocumentLoader
)
from langchain_core.documents import Document


def validate_file_type(filename: str) -> str:
    """Validate and extract file type from filename"""
    allowed_extensions = [
        'txt', 'docx', 'doc', 'pdf', 'md', 'markdown', 'json',
        'pptx', 'ppt', 'xlsx', 'xls', 'csv', 'html', 'rtf', 'odt', 'epub'
    ]
    file_extension = filename.lower().split('.')[-1]

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
        )

    return file_extension


def get_markdown_loader(file_path: str) -> Any:
    """Custom markdown loader with fallback options"""
    try:
        # Try UnstructuredMarkdownLoader first
        return UnstructuredMarkdownLoader(file_path)
    except Exception as e:
        print(f"[WARNING] UnstructuredMarkdownLoader failed: {e}")
        print("[INFO] Falling back to simple text loader for markdown")
        # Fallback to TextLoader which will treat it as plain text
        return TextLoader(file_path, encoding='utf-8')


def get_text_loader_with_encoding(file_path: str) -> Any:
    """Create TextLoader with automatic encoding detection and fallback"""
    # Try different encodings in order of preference
    encodings_to_try = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings_to_try:
        try:
            # Test if the file can be read with this encoding
            with open(file_path, 'r', encoding=encoding) as test_file:
                # Read a small chunk to test the encoding
                test_file.read(1024)
            
            print(f"[FILE_LOADER] Successfully detected encoding: {encoding} for {file_path}")
            return TextLoader(file_path, encoding=encoding)
            
        except (UnicodeDecodeError, UnicodeError) as e:
            print(f"[FILE_LOADER] Encoding {encoding} failed for {file_path}: {e}")
            continue
        except Exception as e:
            print(f"[FILE_LOADER] Unexpected error with encoding {encoding} for {file_path}: {e}")
            continue
    
    # If all encodings fail, try with error handling
    try:
        print(f"[FILE_LOADER] All standard encodings failed, trying utf-8 with error handling")
        return TextLoader(file_path, encoding='utf-8', autodetect_encoding=True)
    except Exception as e:
        print(f"[FILE_LOADER] TextLoader with autodetect failed: {e}")
        # Last resort: create a custom loader that handles encoding errors
        return create_fallback_text_loader(file_path)


def create_fallback_text_loader(file_path: str) -> Any:
    """Create a fallback text loader that handles encoding errors gracefully"""
    class FallbackTextLoader:
        def __init__(self, file_path: str):
            self.file_path = file_path
        
        def load(self):
            """Load the file with robust error handling"""
            try:
                # Try to read with utf-8 and replace errors
                with open(self.file_path, 'r', encoding='utf-8', errors='replace') as file:
                    content = file.read()
                
                # Create a Document object similar to LangChain's TextLoader
                metadata = {"source": self.file_path}
                return [Document(page_content=content, metadata=metadata)]
                
            except Exception as e:
                # If even that fails, try binary mode and decode with errors='ignore'
                print(f"[FALLBACK_LOADER] UTF-8 with replace failed, trying binary mode: {e}")
                try:
                    with open(self.file_path, 'rb') as file:
                        raw_content = file.read()
                    
                    # Try to decode as utf-8, ignoring errors
                    content = raw_content.decode('utf-8', errors='ignore')
                    
                    metadata = {"source": self.file_path}
                    return [Document(page_content=content, metadata=metadata)]
                    
                except Exception as e2:
                    print(f"[FALLBACK_LOADER] All fallback methods failed: {e2}")
                    raise Exception(f"Could not load file {self.file_path}. Tried multiple encodings and fallback methods.")
    
    return FallbackTextLoader(file_path)


def get_doc_loader(file_path: str) -> Any:
    """Custom loader for legacy .doc files using antiword"""
    print(f"[DOC_LOADER] Attempting to load .doc file: {file_path}")

    class AntiwordDocLoader:
        def __init__(self, file_path: str):
            self.file_path = file_path

        def load(self):
            """Load .doc file using antiword command"""
            try:
                result = subprocess.run(
                    ['antiword', self.file_path],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode != 0:
                    raise Exception(f"antiword failed: {result.stderr}")

                content = result.stdout
                if not content.strip():
                    raise Exception("antiword returned empty content")

                print(f"[DOC_LOADER] Successfully extracted {len(content)} characters using antiword")
                metadata = {"source": self.file_path}
                return [Document(page_content=content, metadata=metadata)]

            except FileNotFoundError:
                print(f"[DOC_LOADER] antiword not found, falling back to UnstructuredWordDocumentLoader")
                loader = UnstructuredWordDocumentLoader(self.file_path)
                return loader.load()
            except Exception as e:
                print(f"[DOC_LOADER] antiword failed: {e}, falling back to UnstructuredWordDocumentLoader")
                loader = UnstructuredWordDocumentLoader(self.file_path)
                return loader.load()

    return AntiwordDocLoader(file_path)


def get_odt_loader(file_path: str) -> Any:
    """Custom loader for .odt files using odfpy"""
    print(f"[ODT_LOADER] Attempting to load .odt file: {file_path}")

    class OdfpyLoader:
        def __init__(self, file_path: str):
            self.file_path = file_path

        def load(self):
            """Load .odt file using odfpy"""
            try:
                from odf import text as odf_text
                from odf.opendocument import load as odf_load

                doc = odf_load(self.file_path)

                # Extract all text content
                paragraphs = doc.getElementsByType(odf_text.P)
                content_parts = []

                for para in paragraphs:
                    # Get text content from paragraph
                    para_text = ""
                    for node in para.childNodes:
                        if node.nodeType == node.TEXT_NODE:
                            para_text += str(node)
                        elif hasattr(node, 'childNodes'):
                            for child in node.childNodes:
                                if child.nodeType == child.TEXT_NODE:
                                    para_text += str(child)
                    content_parts.append(para_text)

                content = "\n".join(content_parts)

                if not content.strip():
                    raise Exception("odfpy returned empty content")

                print(f"[ODT_LOADER] Successfully extracted {len(content)} characters using odfpy")
                metadata = {"source": self.file_path}
                return [Document(page_content=content, metadata=metadata)]

            except ImportError:
                print(f"[ODT_LOADER] odfpy not installed, falling back to UnstructuredODTLoader")
                loader = UnstructuredODTLoader(self.file_path)
                return loader.load()
            except Exception as e:
                print(f"[ODT_LOADER] odfpy failed: {e}, falling back to UnstructuredODTLoader")
                loader = UnstructuredODTLoader(self.file_path)
                return loader.load()

    return OdfpyLoader(file_path)


def get_json_loader(file_path: str) -> Any:
    """Create JSON loader with error handling and jq dependency check"""
    print(f"[JSON_LOADER] Attempting to load JSON file: {file_path}")

    # First check if jq is available
    try:
        import jq
        print(f"[JSON_LOADER] jq package is available (version check passed)")
    except ImportError as ie:
        print(f"[JSON_LOADER] jq package not installed: {ie}")
        print(f"[JSON_LOADER] Falling back to text loader for JSON (this works fine for most cases)")
        return get_text_loader_with_encoding(file_path)

    # Try JSONLoader with jq
    try:
        loader = JSONLoader(file_path, jq_schema='.', text_content=False)
        print(f"[JSON_LOADER] Successfully created JSONLoader with jq_schema='.'")
        return loader
    except Exception as e:
        print(f"[JSON_LOADER] JSONLoader failed: {type(e).__name__}: {e}")
        print(f"[JSON_LOADER] Falling back to text loader")
        return get_text_loader_with_encoding(file_path)


def get_loader_for_file_type(file_path: str, file_type: str) -> Any:
    """Factory method to get appropriate LangChain loader with enhanced error handling"""
    loaders = {
        'txt': get_text_loader_with_encoding,
        'docx': Docx2txtLoader,
        'doc': get_doc_loader,  # Custom loader using antiword
        'pdf': PyPDFLoader,
        'json': get_json_loader,
        'pptx': UnstructuredPowerPointLoader,
        'ppt': UnstructuredPowerPointLoader,
        'xlsx': UnstructuredExcelLoader,
        'xls': UnstructuredExcelLoader,  # LibreOffice handles old .xls format
        'csv': CSVLoader,
        'html': UnstructuredHTMLLoader,
        'rtf': UnstructuredRTFLoader,
        'odt': get_odt_loader,  # Custom loader using odfpy
        'epub': UnstructuredEPubLoader,
    }

    # Handle markdown with custom loader that has fallback
    if file_type.lower() in ['md', 'markdown']:
        return get_markdown_loader(file_path)

    loader_factory = loaders.get(file_type.lower())
    if not loader_factory:
        raise ValueError(f"Unsupported file type: {file_type}")

    # Return the loader instance
    return loader_factory(file_path)

