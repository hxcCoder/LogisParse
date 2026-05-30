# Quick Start Guide

## 1. Install & Setup (5 minutes)

```bash
# Navigate to project
cd logisparse

# Activate virtual environment
# Windows:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install dependencies (once per environment)
pip install -r requirements.txt
```

## 2. Configure Environment

Create `.env` file in project root:

```env
# Database
DATABASE_URL=postgresql+asyncpg://logisparse_user:secretpassword@localhost:5432/logisparse_db

# Security
SECRET_KEY=your-super-secret-key-minimum-32-characters-long

# OpenAI (get from https://platform.openai.com/api-keys)
OPENAI_API_KEY=sk-...

# Optional
DEBUG=False
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

## 3. Database Setup (with Docker)

```bash
# Start PostgreSQL container
docker-compose up -d

# Run migrations
alembic upgrade head
```

## 4. Run the API

```bash
# Development mode (auto-reload)
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

API will be available at: **http://localhost:8000**  
Docs: **http://localhost:8000/docs**

## 5. Run Tests

```bash
# All tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=app --cov-report=html

# Specific test file
pytest tests/unit/test_security.py -v
```

---

## Common Tasks

### Create a new user
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure-password",
    "full_name": "John Doe"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "secure-password"
  }'
```

### Upload a document
```bash
TOKEN="<access_token_from_login>"

curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@path/to/document.pdf"
```

### Check document status
```bash
TOKEN="<access_token>"
DOC_ID="<document_id>"

curl http://localhost:8000/api/v1/documents/$DOC_ID \
  -H "Authorization: Bearer $TOKEN"
```

---

## Troubleshooting

**ImportError: No module named 'fastapi'**  
→ Activate virtual environment: `.venv\Scripts\Activate.ps1`  
→ Install deps: `pip install -r requirements.txt`

**Database connection refused**  
→ Start Docker: `docker-compose up -d`  
→ Check status: `docker ps`

**OpenAI API errors**  
→ Check OPENAI_API_KEY is set in `.env`  
→ Verify API key has access to Structured Outputs

**Port 8000 already in use**  
→ Use different port: `uvicorn app.main:app --port 8001 --reload`

---

## Development Workflow

```bash
# Code formatting
black app/ tests/

# Type checking
mypy app/

# Linting
ruff check app/

# All checks at once
make lint  # (if Makefile is available)
```
