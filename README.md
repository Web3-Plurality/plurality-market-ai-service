# RAG API with FastAPI, LangChain, and Pinecone

This project implements a Retrieval-Augmented Generation (RAG) API using FastAPI, LangChain, and Pinecone for vector storage.

## Prerequisites

- Python 3.13 or higher
- Pinecone API key
- Google API key (for Gemini)

## Setup

1. Clone the repository:

```bash
git clone https://github.com/Web3-Plurality/aI-agents-poc.git
cd aI-agents-poc
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install system dependencies (required for file processing):

### Windows

#### Antiword (Required for legacy .doc files)

1. Download antiword from: https://sourceforge.net/projects/open-egov/files/Compiled%20OSS%20Packages/windows-32/antiword-0.37.7z/download
2. Extract the archive to `C:\Program Files\antiword-0.37\`
3. Add `C:\Program Files\antiword-0.37\bin` to your system PATH:
   - Open System Properties → Advanced → Environment Variables
   - Under "System variables", find `Path` and click Edit
   - Add `C:\Program Files\antiword-0.37\bin`
   - Click OK
4. Set the `ANTIWORDHOME` environment variable:
   - In Environment Variables, under "System variables", click New
   - Variable name: `ANTIWORDHOME`
   - Variable value: `C:\Program Files\antiword-0.37\share\antiword`
   - Click OK
5. Restart your terminal

#### LibreOffice (Required for .doc, .ppt, .xls file support)

Using Chocolatey:
```bash
choco install libreoffice-fresh -y
```

Or download from: https://www.libreoffice.org/download/

#### Pandoc (Required for EPUB and document conversion)

Using Chocolatey:
```bash
choco install pandoc -y
```

Or download from: https://pandoc.org/installing.html

### macOS

```bash
brew install antiword
brew install --cask libreoffice
brew install pandoc
```

### Linux (Debian/Ubuntu)

```bash
sudo apt-get install antiword libreoffice pandoc libmagic1
```

> **Note:** After installing these dependencies on Windows, restart your terminal to ensure all tools are available in PATH.

5. Create a `.env` file in the project root with your API keys:
```env
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENV=your_pinecone_environment
GOOGLE_API_KEY=your_google_api_key
```

## Running the Application

Start the FastAPI server on port **8001** (the market stack's AI service port — keeps it
out of collision with prod's AI service on 8000):

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

The API will be available at:
- API endpoints: http://localhost:8001
- API documentation: http://localhost:8001/docs

> The `--port 8001` flag is **required** — uvicorn defaults to 8000 if you omit it, which
> collides with the prod AI service and breaks `market-backend`'s `AI_SERVICE_URL`. Always
> include it when restarting.


## Environment Variables

- `PINECONE_API_KEY`: Your Pinecone API key
- `PINECONE_ENV`: Your Pinecone environment
- `GOOGLE_API_KEY`: Your Google API key for Gemini


## Docker
   docker build -t context-service .
   docker run -p 8000:8000 --env-file .env context-service
      docker run -p 8000:8000 \
     -e PINECONE_API_KEY=your_key \
     -e GOOGLE_API_KEY=your_key \
     -e CONTEXT_API_KEY=your_key \
     context-service
## License

Hers the Colab Link:
https://colab.research.google.com/drive/1zf1IxAjMWVwY_XFm7azfQhCUzs1Y3C1p?usp=sharing
