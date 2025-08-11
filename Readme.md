### OppTrackGraph API

Python/FastAPI service for opportunity insights, embeddings, PDF processing (with OCR fallback), and Supabase-backed storage.

### Prerequisites
- Python 3.11+ (Docker image uses 3.13)
- macOS or Linux
- For PDF OCR and LaTeX features:
  - macOS: install MacTeX or BasicTeX (provides `pdflatex`), and Tesseract
    - `brew install --cask mactex` or `brew install --cask basictex`
    - `brew install tesseract poppler`
  - Linux (Debian/Ubuntu):
    - `sudo apt-get update && sudo apt-get install -y texlive-latex-base texlive-latex-extra tesseract-ocr poppler-utils`

### Setup
1) Create and activate a virtualenv

```bash
python -m venv venv
. venv/bin/activate
```

2) Install requirements

```bash
# macOS
pip install -r requirements-mac.txt

# Linux
pip install -r requirements-linux.txt
```

3) Configure environment variables in `.env` (example keys)

```env
LLM_API_BASE_URL=...
LLM_MODEL_NAME=...
LLM_API_KEY=...
EMBEDDING_API_BASE_URL=...
EMBEDDING_MODEL_NAME=...
EMBEDDING_API_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_ANON_KEY=...
SUPABASE_PASSWORD=...
SUPABASE_HOST=...
POSTGRES_DB_NAME=...
POSTGRES_DB_USER=...
POSTGRES_DB_PASSWORD=...
POSTGRES_DB_HOST=...
POSTGRES_DB_PORT=...
```

### Run (local)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Then open `http://localhost:8080/health`.

### Scripts
- `scripts/run_app.sh`: creates venv if missing, installs requirements, runs the API
- `scripts/run_tests.sh`: installs test packages and runs pytest with coverage

### Docker

Build and run:

```bash
docker build -t opptrackgraph .
docker run --rm --env-file .env -p 8080:8080 opptrackgraph
```

The image installs LaTeX, Tesseract and Poppler, and downloads NLTK data at build time.

### Testing

```bash
. venv/bin/activate
./scripts/run_tests.sh
```

### Endpoints
- `GET /health` — service health
- `GET /config/check` — show which config keys are present (masked)
- `GET /insights/industries?limit=N`
- `GET /insights/industry?account_industry=...&limit=N`

### Notes
- Supabase is used for auth and storage; configure keys in `.env`.
- Database connections use `asyncpg` via SQLAlchemy.