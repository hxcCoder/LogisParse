# LogisParse - Logistics Document Automation SaaS
[![CI](https://github.com/hxcCoder/LogisParse/actions/workflows/ci.yml/badge.svg)](https://github.com/hxcCoder/LogisParse/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/hxcCoder/LogisParse/branch/main/graph/badge.svg)](https://codecov.io/gh/hxcCoder/LogisParse)

Backend API for automatic extraction of logistics data from PDFs and images using OpenAI's Structured Outputs.

**Status:** Production-ready MVP  
**Stack:** Python 3.12 + FastAPI + PostgreSQL + OpenAI

---
## Status
N
## Architecture: Dependency Injection (DI)

This project follows **explicit dependency injection** patterns:

**No global state** - Settings and database are injected via `Depends()`  
**Testable** - All dependencies can be overridden with `app.dependency_overrides`  
**Async-first** - Full async/await support with SQLAlchemy 2.0  
**Clean separation** - Infrastructure decoupled from business logic  

### Key Files

- `app/core/config.py` - Settings with `@lru_cache` (no global instances)
- `app/core/database.py` - Pure functions: `build_engine()`, `build_session_maker()`
- `app/api/deps.py` - Dependency injection functions: `get_settings_dep()`, `get_db()`
- `app/main.py` - App startup with lifespan context manager (stores engine/sessionmaker in `app.state`)
- `tests/conftest.py` - Test fixtures with `app.dependency_overrides`

---

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 16+
- OpenAI API Key

### Installation

```bash
cd logisparse
python -m venv .venv
source .venv/bin/activate          # On Windows: .venv\Scripts\Activate.ps1
pip install -e .
```

### Environment Variables

Create `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/logisparse_db
SECRET_KEY=your-secret-key-min-32-chars
OPENAI_API_KEY=sk-...
```

### Running

```bash
# Development server (auto-reload)
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v

# Format code
black app/

# Check types
mypy app/
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
- `GET /ready` - Readiness check
- `GET /` - Root info

---

## Dependency Injection Pattern

### How It Works

**1. Settings (no global state)**
```python
# In api/deps.py
def get_settings_dep() -> Settings:
    return get_settings()  # @lru_cache cached, pure function

# Usage in endpoint
@router.get("/config")
async def show_config(
    settings: Annotated[Settings, Depends(get_settings_dep)]
) -> dict:
    return {"version": settings.APP_VERSION}
```

**2. Database (dependency injection)**
```python
# In api/deps.py
async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    session_maker = request.app.state.session_maker
    async with session_maker() as session:
        yield session

# Usage in endpoint
@router.get("/documents")
async def list_documents(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> list:
    documents = await get_user_documents(db, current_user.id)
    return documents
```

**3. Application Startup (lifespan)**
```python
# In main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    engine = build_engine(settings)
    session_maker = build_session_maker(engine)
    app.state.engine = engine
    app.state.session_maker = session_maker
    
    yield
    
    # Shutdown
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
```

---

## Testing with Isolation

**conftest.py** demonstrates proper test isolation:

```python
@pytest.fixture
def test_settings() -> Settings:
    """Fake settings for testing"""
    return Settings(DATABASE_URL="sqlite+aiosqlite:///:memory:", ...)

@pytest.fixture
def override_get_db(db_session):
    """Override get_db with in-memory SQLite"""
    app.dependency_overrides[get_db] = lambda: (yield db_session)
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def override_get_settings(test_settings):
    """Override get_settings_dep with test settings"""
    app.dependency_overrides[get_settings_dep] = lambda: test_settings
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def client(override_get_db, override_get_settings):
    """Test client with all overrides active"""
    return TestClient(app)
```

**Test example:**
```python
def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

---

## Why This Architecture?

| Problem | Solution |
|---------|----------|
| Import-time side effects | Settings are functions, not globals |
| Circular dependencies | Dependencies injected at request time |
| Pytest failures | All dependencies can be mocked |
| Hard to test | Pure functions + dependency overrides |
| Database coupling | DB accessed only via `get_db()` dependency |

---

## Project Structure

```
app/
├── api/v1/              # HTTP routes (auth, documents)
│   └── deps.py          # Dependency injection functions
├── core/                # Configuration and infrastructure
│   ├── config.py        # Settings (@lru_cache)
│   ├── database.py      # Engine/sessionmaker builders
│   ├── security.py      # JWT, password hashing
│   └── middleware.py    # Request processing
├── crud/                # Database operations
├── models/              # SQLAlchemy ORM
├── schemas/             # Pydantic validation
└── services/            # Business logic (AI extraction)

tests/
├── conftest.py          # Test fixtures and overrides
├── unit/                # Unit tests (schemas, security, etc)
└── integration/         # API endpoint tests
```

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

## Running with Docker

```bash
docker-compose up -d
# API: http://localhost:8000
# Database: postgres://logisparse_user@localhost:5432/logisparse_db
```

---

## Key Features

✅ JWT authentication with Argon2  
✅ Multi-file upload (PDF, PNG, JPG)  
✅ AI-powered data extraction (OpenAI gpt-4o-mini)  
✅ Structured outputs with Pydantic validation  
✅ Async everything (FastAPI + SQLAlchemy)  
✅ Request tracking via X-Request-ID header  
✅ Rate limiting and CORS configured  
✅ Dependency Injection testing  
✅ Complete type safety with Annotated types  

---

## Development

```bash
# Format
black app/ tests/

# Type check
mypy app/

# Lint
pylint app/

# Test
pytest tests/ -v
```
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
