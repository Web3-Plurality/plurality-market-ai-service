# Plurality Market AI Service

FastAPI service that handles vector indexing, retrieval, and LLM-backed query over user memory contexts for the Plurality marketplace stack. Called by `plurality-market-backend` on context add/upload/delete and on the MCP `search_memory` path.

Note on BYOK: user-supplied LLM keys live entirely in the frontend (the browser calls LLM providers directly); this service always uses the server-side `GOOGLE_API_KEY` for its own extraction/summarization calls.

Stack:
- **FastAPI** for the HTTP surface (port `8001`)
- **LangChain + Google Gemini** for LLM calls (model id from `GEMINI_MODEL`, default `gemini-3.6-flash`; Google retires ids for new accounts, so bump the env var when a 404 "no longer available to new users" shows up)
- **HuggingFace BGE** (`BAAI/bge-large-en-v1.5`) for embeddings, run locally on CPU
- **AWS S3 Vectors** for the vector store (multi-tenant via `NAMESPACE_PREFIX`)
- **Postgres** for context-row lookups and orphan-vector validation

## Skills

A bucket's optional Skill instructions live in the backend (the `skillInstructions` column on `user_ai_profile`) and are not vectorised; this service only indexes the bucket's memory (contexts).

## Prerequisites

- Python 3.11+ (`Dockerfile` pins `python:3.11-slim`)
- Google API key for Gemini
- AWS credentials with S3 Vectors access (bucket + index pre-provisioned)
- Reachable Postgres instance with the `user_context` table (provided by `plurality-market-backend`)

## Setup

1. Clone the repository (assuming you're working inside the market stack monorepo layout; otherwise replace the URL with your remote):

```bash
git clone <your-remote-for-plurality-market-ai-service>
cd plurality-market-ai-service
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

5. Create a `.env` file in the project root. Required variables:

```env
# LLM
GOOGLE_API_KEY=your_google_api_key
# Optional model overrides (defaults: gemini-3.6-flash; ADVANCED falls back to GEMINI_MODEL)
GEMINI_MODEL=gemini-3.6-flash
GEMINI_MODEL_ADVANCED=

# AWS S3 Vectors (vector store)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-2
S3_VECTOR_BUCKET_NAME=your_s3_vector_bucket_name
S3_VECTOR_INDEX_NAME=your_s3_vector_index_name

# Multi-tenant namespace prefix. Empty string for single-tenant deployments;
# "market:" isolates this stack's vectors from any shared S3 Vectors instance.
NAMESPACE_PREFIX=market:

# Postgres (must match the database that plurality-market-backend writes to)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=plurality_market
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# Authentication for inbound requests + outbound webhooks to the backend
CONTEXT_API_KEY=shared_secret_between_this_service_and_market_backend
BACKEND_API_URL=http://localhost:5001
BACKEND_API_KEY=shared_secret_for_webhook_callbacks
```

> The full list of variables the code reads is defined in `app/config/settings.py`.

## Running the Application

Start the FastAPI server on port **8001** (the market stack's AI service port; keeps it
out of collision with prod's AI service on 8000).

Use the venv's Python directly with `-m uvicorn`. This bypasses PATH entirely and is
immune to the common mistake of accidentally invoking `uvicorn` from a different venv
(any other Python project with `uvicorn` installed will shadow this one on PATH):

**Windows PowerShell:**
```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**macOS / Linux:**
```bash
./venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

If you've activated this venv (`venv\Scripts\Activate.ps1` / `source venv/bin/activate`)
and the prompt shows `(venv)`, the shorter form works too:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

The API will be available at:
- API endpoints: http://localhost:8001 (all routes live under the `/rag` prefix, e.g. `/rag/add-context`)
- API documentation: http://localhost:8001/docs

> The `--port 8001` flag is **required**: uvicorn defaults to 8000 if you omit it, which
> collides with the prod AI service and breaks `market-backend`'s `AI_SERVICE_URL`. Always
> include it when restarting.

### Troubleshooting: `ModuleNotFoundError: No module named 'langchain_google_genai'`

If you see this with a traceback pointing at a *different* venv's `site-packages`
(e.g. `test-project\.venv\Lib\site-packages\uvicorn`), uvicorn is being loaded from the
wrong Python install. This happens when `uvicorn` resolves on PATH to another project's
venv. Use the explicit `.\venv\Scripts\python.exe -m uvicorn` form above; it ignores
PATH entirely and forces uvicorn to load from *this* project's venv.

If the explicit form gives the same error, the AI service's venv itself is missing the
dependency. Install:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```


## Environment Variables

See the Setup `.env` block above for the complete list. A quick map by purpose:

| Group | Variables |
|---|---|
| LLM | `GOOGLE_API_KEY`, `GEMINI_MODEL`, `GEMINI_MODEL_ADVANCED` |
| Vector store | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_VECTOR_BUCKET_NAME`, `S3_VECTOR_INDEX_NAME`, `NAMESPACE_PREFIX` |
| Postgres | `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` |
| Auth | `CONTEXT_API_KEY` (gate on inbound calls), `BACKEND_API_URL`, `BACKEND_API_KEY` (for outbound webhook callbacks) |

`NAMESPACE_PREFIX` should be `market:` to keep this stack's vectors isolated when sharing an S3 Vectors instance with another deployment; set it to empty string for a dedicated instance.

## Docker

The `Dockerfile` is `python:3.11-slim` based and includes the system dependencies (pandoc, libreoffice, libmagic) needed for document loaders.

```bash
docker build -t plurality-market-ai-service .
docker run -p 8001:8001 --env-file .env plurality-market-ai-service
```

The container listens on `8001` to match the `BACKEND_API_URL → AI_SERVICE_URL` wiring in `plurality-market-backend`.

## License

MIT.
