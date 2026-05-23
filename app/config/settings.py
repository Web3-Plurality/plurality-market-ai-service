import os
from dotenv import load_dotenv
# Download required NLTK data
import nltk
import ssl
# Load environment variables
load_dotenv()
# Handle SSL certificate issues that might occur during NLTK downloads
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download required NLTK data for UnstructuredMarkdownLoader
def download_nltk_data():
    """Download required NLTK data packages"""
    import nltk.downloader
    
    required_packages = [
        'punkt',
        'averaged_perceptron_tagger', 
        'averaged_perceptron_tagger_eng',
        'stopwords',
        'wordnet',
        'omw-1.4'
    ]
    
    downloader = nltk.downloader.Downloader()
    
    for package in required_packages:
        try:
            # Check if package is already installed using NLTK's downloader
            if downloader.is_installed(package):
                print(f"NLTK package {package} already available")
            else:
                print(f"Downloading NLTK package: {package}")
                result = nltk.download(package, quiet=True)
                if result:
                    print(f"Successfully downloaded NLTK package: {package}")
                else:
                    print(f"Failed to download NLTK package: {package}")
        except Exception as e:
            print(f"Warning: Error with NLTK package {package}: {e}")


class Settings:
    """Application settings and configuration"""
    download_nltk_data()
    # API Configuration
    API_KEY: str = os.getenv("CONTEXT_API_KEY", "dev-key-12345")
    
    # Database Configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME")
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    
    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-2")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY")

    # AWS Bedrock Configuration (can use same or different credentials)
    AWS_BEDROCK_REGION: str = os.getenv("AWS_BEDROCK_REGION", "us-east-1")
    AWS_BEDROCK_ACCESS_KEY_ID: str = os.getenv("AWS_BEDROCK_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID"))
    AWS_BEDROCK_SECRET_ACCESS_KEY: str = os.getenv("AWS_BEDROCK_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY"))
    
    # S3 Vectors Configuration
    S3_VECTOR_BUCKET_NAME: str = os.getenv("S3_VECTOR_BUCKET_NAME", "plurality-ocl")
    S3_VECTOR_INDEX_NAME: str = os.getenv("S3_VECTOR_INDEX_NAME", "index")

    # Tenant prefix written into every vector's metadata.namespace and added
    # to every query filter. Lets the market-* stack share prod's vector DB
    # without risk of cross-stack reads/writes/deletes. Empty string disables
    # the prefix entirely (e.g. when the market stack moves to its own bucket).
    NAMESPACE_PREFIX: str = os.getenv("NAMESPACE_PREFIX", "")
    
    # Google API Configuration
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    GOOGLE_SEARCH_API_KEY: str = os.getenv("GOOGLE_SEARCH_API_KEY")  # Can be same as GOOGLE_API_KEY
    GOOGLE_SEARCH_ENGINE_ID: str = os.getenv("GOOGLE_SEARCH_ENGINE_ID")  # Custom Search Engine ID (CX)

    # Application Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    EMBEDDING_BATCH_SIZE: int = 32
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_WORKERS: int = 4
    
    @property
    def db_config(self) -> dict:
        """Get database configuration as dictionary"""
        return {
            'host': self.DB_HOST,
            'port': self.DB_PORT,
            'database': self.DB_NAME,
            'user': self.DB_USER,
            'password': self.DB_PASSWORD
        }

# Create settings instance
settings = Settings() 