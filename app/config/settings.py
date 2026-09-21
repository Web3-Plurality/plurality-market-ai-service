import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def download_nltk_data():
    """Download required NLTK data packages (used by UnstructuredMarkdownLoader).

    Invoked from the FastAPI startup hook in app.main — NOT at import time —
    so importing this module stays offline/CI safe.
    """
    import nltk
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
    # API Configuration — fail closed: this key gates every inbound request.
    API_KEY: str = os.getenv("CONTEXT_API_KEY", "")
    if not API_KEY:
        raise RuntimeError(
            "CONTEXT_API_KEY must be set (shared secret between this service and the backend)"
        )

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

    # S3 Vectors Configuration
    S3_VECTOR_BUCKET_NAME: str = os.getenv("S3_VECTOR_BUCKET_NAME", "your-vector-bucket")
    S3_VECTOR_INDEX_NAME: str = os.getenv("S3_VECTOR_INDEX_NAME", "index")

    # Tenant prefix written into every vector's metadata.namespace and added
    # to every query filter. Lets the market-* stack share prod's vector DB
    # without risk of cross-stack reads/writes/deletes. Defaults to "market:"
    # so a machine with the var UNSET can never silently write into the
    # shared keyspace; set it to an explicit empty string only on a bucket
    # dedicated to this stack.
    NAMESPACE_PREFIX: str = os.getenv("NAMESPACE_PREFIX", "market:")

    # Google API Configuration
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY")
    # Gemini model IDs. Configurable because Google gates model generations
    # per account: keys from accounts created after the mid-2026 key
    # migration ("AQ." keys) get 404 "no longer available to new users" on
    # gemini-2.x, so a hard-coded model breaks on key rotation. Defaults to
    # the current stable fast model; GEMINI_MODEL_ADVANCED falls back to it.
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
    GEMINI_MODEL_ADVANCED: str = os.getenv("GEMINI_MODEL_ADVANCED") or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    # Application Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    EMBEDDING_BATCH_SIZE: int = 32

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
