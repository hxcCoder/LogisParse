# LogisParse - Logistics Document Automation SaaS

Backend API for automatic extraction of logistics data from PDFs and images using OpenAI's Structured Outputs.

**Status:** Production-ready MVP  
**Stack:** Python 3.12 + FastAPI + PostgreSQL + OpenAI

---

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 16+
- OpenAI API Key

### Setup

```bash
# Clone and install
git clone <repo>
cd logisparse

# Using setup script (recommended)
python setup.py

# Or manually
python -m venv .venv
source .venv/bin/activate          # On Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Environment Variables

Create `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/logisparse_db
SECRET_KEY=your-secret-key-min-32-chars
OPENAI_API_KEY=sk-...
```

### Running

```bash
# Start development server
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v

# Format code
black app/

# Check types
mypy app/
```

### With Docker

```bash
docker-compose up -d
# API runs on http://localhost:8000
# Database: postgres://logisparse_user@localhost:5432/logisparse_db
```

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Create account
- `POST /api/v1/auth/login` - Get access token

### Documents
- `POST /api/v1/documents/upload` - Upload PDF/image
- `GET /api/v1/documents` - List user's documents (paginated)
- `GET /api/v1/documents/{id}` - Get document with extracted data

### Health
- `GET /health` - Health check

---

## Project Structure

```
app/
├── api/v1/          # HTTP routes (auth, documents)
├── core/            # Configuration, database, security
├── models/          # SQLAlchemy ORM (users, documents)
├── schemas/         # Pydantic validation (input/output)
├── crud/            # Database operations
└── services/        # Business logic (AI extraction)

tests/
├── unit/            # Security, validation, CRUD tests
└── integration/     # API endpoint tests
```

---

## Features

✅ JWT authentication with bcrypt  
✅ Multi-file upload (PDF, PNG, JPG)  
✅ AI-powered data extraction (OpenAI gpt-4o-mini)  
✅ Structured outputs with Pydantic validation  
✅ Async everything (FastAPI + SQLAlchemy)  
✅ Request tracking via X-Request-ID header  
✅ Rate limiting and CORS configured  
✅ Comprehensive test coverage  

---

## Database Schema

### users
- `id` (UUID, PK)
- `email` (String, unique)
- `hashed_password` (String)
- `full_name` (String)
- `is_active` (Boolean)
- `created_at` (DateTime)

### documents
- `id` (UUID, PK)
- `user_id` (UUID, FK → users)
- `filename` (String)
- `content_type` (String)
- `status` (Enum: PENDING, PROCESSING, EXTRACTED, FAILED)
- `extracted_data` (JSONB, nullable)
- `error_logs` (Text, nullable)
- `uploaded_at` (DateTime)
- `processed_at` (DateTime, nullable)

---

## Extracted Data Schema

When a document is successfully processed, the `extracted_data` field contains:

```json
{
  "origen": "Puerto Montt",
  "destino": "Puerto Varas",
  "patente_camion": "ABC-1234",
  "fecha_despacho": "2026-05-29",
  "items": [
    {"sku": "SALMON-001", "cantidad": 100}
  ]
}
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app

# Run specific test file
pytest tests/unit/test_security.py -v

# Run integration tests only
pytest tests/integration/ -v
```

---

## Configuration

See `app/core/config.py` for all environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key (min 32 chars)
- `OPENAI_API_KEY`: OpenAI API credentials
- `DEBUG`: Enable debug mode (default: False)
- `CORS_ORIGINS`: Allowed origins (default: localhost)

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design
- [AI Extraction](docs/AI_EXTRACTION.md) - Extraction pipeline details

---

## License

Proprietary - CORFO Challenge 2026
- Alembic
- Pydantic v2
- JWT auth
- OpenAI Responses API + Structured Outputs
- Docker / Docker Compose
- Ruff, Black, mypy, pytest, pre-commit

## System Flow

```mermaid
sequenceDiagram
  participant U as User
  participant API as FastAPI
  participant DB as PostgreSQL
  participant AI as OpenAI

  U->>API: POST /api/v1/documents/upload
  API->>API: Validate JWT, size, extension, magic bytes
  API->>DB: Create document PENDING
  API->>DB: Mark PROCESSING
  API->>AI: Send PDF/image as file input
  AI-->>API: Structured extraction
  API->>DB: Store JSON and mark EXTRACTED
  API-->>U: Document response
```

## Quickstart

```bash
cp .env.example .env
docker compose up --build
```

Open:

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/api/docs`
- Health: `http://localhost:8000/health`

## Local Development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pre-commit install
alembic upgrade head
uvicorn app.main:app --reload
```

Useful commands:

```bash
make test
make lint
make format
make typecheck
make migrate
```

## Environment

Required in production:

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Async PostgreSQL connection URL |
| `SECRET_KEY` | JWT signing secret, 32+ random bytes |
| `OPENAI_API_KEY` | OpenAI API key for extraction |
| `ALLOWED_ORIGINS` | Comma-separated CORS allowlist |
| `ENVIRONMENT` | `development`, `staging` or `production` |

See `.env.example` for the full list.

## API Overview

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/register` | No | Create a user |
| `POST` | `/api/v1/auth/login` | No | Return JWT |
| `POST` | `/api/v1/documents/upload` | Yes | Upload and process a document |
| `GET` | `/api/v1/documents` | Yes | List own documents |
| `GET` | `/api/v1/documents/{id}` | Yes | Read own document |
| `GET` | `/health` | No | Liveness check |
| `GET` | `/ready` | No | Readiness check |

## Testing

```bash
pytest
```

Current coverage focus:

- Auth token and password behavior.
- Upload validation.
- Critical document endpoints.
- AI request shape for PDF/image inputs.

## Deployment

The simplest production path is one API container plus managed PostgreSQL.

Good initial targets:

- VPS with Docker Compose.
- Railway.
- Render.
- Hetzner + Coolify.
- Dokploy.

Avoid Kubernetes, service splitting and queues until document volume or reliability requirements justify them.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [AI Extraction Pipeline](docs/AI_EXTRACTION.md)
- [Development Conventions](docs/DEVELOPMENT.md)
- [Production Checklist](docs/PRODUCTION.md)
- [Roadmap](docs/ROADMAP.md)
- [Audit](docs/AUDIT.md)
- [ADR 0001: Modular Monolith](docs/adr/0001-modular-monolith.md)
- [ADR 0002: OpenAI Responses API](docs/adr/0002-openai-responses-api.md)

## Screenshots

Screenshots will be added once the frontend exists.

```text
docs/assets/screenshots/
  upload-flow.png
  extraction-result.png
  document-history.png
```

## Product Philosophy

Build the narrow product customers can trust:

- One backend.
- One database.
- Clear contracts.
- Strong validation.
- Useful logs.
- Cheap deployment.
- No platform complexity before product pull.

## License

TBD by the project owner.

## Author

LogisParse project, Patagonia / Los Lagos, Chile.
