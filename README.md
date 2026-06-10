# LogisParse

### Logistics Document Automation Platform

Backend SaaS focused on automatic extraction and normalization of logistics data from PDFs and images using AI.

[![CI](https://github.com/hxcCoder/LogisParse/actions/workflows/ci.yml/badge.svg)](https://github.com/hxcCoder/LogisParse/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/hxcCoder/LogisParse/branch/main/graph/badge.svg)](https://codecov.io/gh/hxcCoder/LogisParse)

---

# Overview

LogisParse is a backend-first platform designed to automate repetitive logistics document processing.

Companies upload transport documents, dispatch guides, invoices, manifests or scanned PDFs, and the system extracts structured logistics data automatically using OpenAI Structured Outputs.

The goal is simple:

* Reduce manual data entry.
* Standardize logistics information.
* Minimize human errors.
* Accelerate operational workflows.
* Keep infrastructure lightweight and affordable.

---

# What Problem Does It Solve?

Many logistics and transport companies still process documents manually.

Operators often:

* Read PDFs manually.
* Copy data into Excel or ERP systems.
* Validate truck plates and shipment dates manually.
* Lose time correcting extraction mistakes from traditional OCR systems.

LogisParse automates that workflow through AI-powered structured extraction.

---

# Core Features

✅ JWT authentication
✅ Multi-user support
✅ PDF and image upload
✅ AI extraction using OpenAI Structured Outputs
✅ Strong schema validation with Pydantic v2
✅ Async architecture with FastAPI + SQLAlchemy 2.0
✅ PostgreSQL persistence
✅ Request tracking with X-Request-ID
✅ Docker-ready deployment
✅ Full dependency injection architecture
✅ High testability and isolated testing
✅ Type-safe backend with mypy

---

# Example Extraction

## Input

A logistics dispatch document uploaded as PDF or image.

## Output

```json
{
  "origen": "Puerto Montt",
  "destino": "Puerto Varas",
  "patente_camion": "ABC-1234",
  "fecha_despacho": "2026-05-29",
  "items": [
    {
      "sku": "SALMON-001",
      "cantidad": 100
    }
  ]
}
```

---

# System Flow

```text
 ┌─────────────────────┐
 │      USER           │
 │ Uploads PDF/Image   │
 └──────────┬──────────┘
            │
            ▼
 ┌─────────────────────┐
 │      FASTAPI API    │
 │ Auth + Validation   │
 └──────────┬──────────┘
            │
            ▼
 ┌─────────────────────┐
 │  DOCUMENT PIPELINE  │
 │ Status Management   │
 │ Processing Control  │
 └──────────┬──────────┘
            │
            ▼
 ┌─────────────────────┐
 │      OPENAI API     │
 │ Structured Outputs  │
 └──────────┬──────────┘
            │
            ▼
 ┌─────────────────────┐
 │    POSTGRESQL DB    │
 │ Structured JSON     │
 └──────────┬──────────┘
            │
            ▼
 ┌─────────────────────┐
 │   CLIENT RESPONSE   │
 │ Extracted Logistics │
 │        Data         │
 └─────────────────────┘
```

---

# Architecture Philosophy

LogisParse follows a **clean modular monolith architecture**.

The project intentionally avoids premature complexity:

* No microservices.
* No Kubernetes.
* No distributed queues.
* No unnecessary abstractions.

Instead, the focus is:

* Reliability.
* Maintainability.
* Scalability when necessary.
* Fast iteration speed.
* Low infrastructure cost.

---

# Dependency Injection Architecture

The backend uses explicit dependency injection patterns for maximum testability and maintainability.

## Why DI?

Traditional FastAPI projects often suffer from:

* Global state.
* Circular imports.
* Hard-to-test services.
* Tight database coupling.

LogisParse avoids these problems through dependency injection.

---

# Dependency Flow

```text
Request
   │
   ▼
FastAPI Route
   │
   ├── Inject Settings
   │
   ├── Inject Database Session
   │
   └── Inject Current User
            │
            ▼
      Business Logic
            │
            ▼
        Database
```

---

# Example Dependency Injection

## Settings Injection

```python
def get_settings_dep() -> Settings:
    return get_settings()

@router.get("/config")
async def show_config(
    settings: Annotated[Settings, Depends(get_settings_dep)]
):
    return {"version": settings.APP_VERSION}
```

## Database Injection

```python
async def get_db(request: Request):
    session_maker = request.app.state.session_maker

    async with session_maker() as session:
        yield session
```

---

# Project Structure

```text
app/
├── api/v1/
│   ├── auth/
│   ├── documents/
│   └── deps.py
│
├── core/
│   ├── config.py
│   ├── database.py
│   ├── security.py
│   └── middleware.py
│
├── crud/
├── models/
├── schemas/
├── services/
└── main.py

tests/
├── unit/
├── integration/
└── conftest.py
```

---

# Tech Stack

| Layer            | Technology           |
| ---------------- | -------------------- |
| API Framework    | FastAPI              |
| Language         | Python 3.12          |
| Database         | PostgreSQL           |
| ORM              | SQLAlchemy 2.0       |
| Validation       | Pydantic v2          |
| AI Extraction    | OpenAI Responses API |
| Auth             | JWT + Argon2         |
| Containerization | Docker               |
| Migrations       | Alembic              |
| Testing          | Pytest               |
| Formatting       | Ruff + Black         |
| Type Checking    | mypy                 |

---

# API Endpoints

## Authentication

| Method | Endpoint                | Description    |
| ------ | ----------------------- | -------------- |
| POST   | `/api/v1/auth/register` | Create account |
| POST   | `/api/v1/auth/login`    | Generate JWT   |

## Documents

| Method | Endpoint                   | Description       |
| ------ | -------------------------- | ----------------- |
| POST   | `/api/v1/documents/upload` | Upload document   |
| GET    | `/api/v1/documents`        | List documents    |
| GET    | `/api/v1/documents/{id}`   | Retrieve document |

## Health Checks

| Method | Endpoint  |
| ------ | --------- |
| GET    | `/health` |
| GET    | `/ready`  |

---

# Database Design

## users

```text
id
email
hashed_password
full_name
is_active
created_at
```

## documents

```text
id
user_id
filename
content_type
status
extracted_data
error_logs
uploaded_at
processed_at
```

---

# Processing States

```text
PENDING
   │
   ▼
PROCESSING
   │
   ├── EXTRACTED
   │
   └── FAILED
```

---

# Testing Strategy

The project emphasizes isolated and reliable testing.

## Coverage Focus

* Authentication logic.
* Upload validation.
* AI extraction requests.
* Critical API endpoints.
* Database behavior.
* Security flows.

## Example

```bash
pytest tests/ --cov=app
```

---

# Docker Deployment

## Development

```bash
docker compose up --build
```

## Services

| Service    | Port |
| ---------- | ---- |
| API        | 8000 |
| PostgreSQL | 5432 |

---

# Production Philosophy

LogisParse is optimized for practical deployment.

Recommended early-stage infrastructure:

* VPS + Docker Compose
* Railway
* Render
* Hetzner + Coolify
* Dokploy

Avoid scaling complexity until actual customer demand requires it.

---

# Product Vision

LogisParse aims to become a lightweight logistics intelligence platform for small and medium logistics companies in Chile and Latin America.

The objective is not to build a massive enterprise platform immediately.

The objective is to build:

* A reliable tool.
* A narrow product.
* A system operators trust.
* A backend simple enough to maintain.
* A SaaS affordable to deploy and scale.

---

# Quickstart

## Local Setup

```bash
git clone https://github.com/hxcCoder/LogisParse.git

cd LogisParse

python -m venv .venv

source .venv/bin/activate
# Windows:
# .venv\Scripts\Activate.ps1

pip install -e .
```

## Environment Variables

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/logisparse_db

SECRET_KEY=your-secret-key

OPENAI_API_KEY=sk-...
```

## Run

```bash
uvicorn app.main:app --reload
```

---

# Documentation

```text
docs/
├── ARCHITECTURE.md
├── AI_EXTRACTION.md
├── DEVELOPMENT.md
├── PRODUCTION.md
├── ROADMAP.md
└── AUDIT.md
```

---

# Screenshots

Frontend screenshots will be added in future iterations.

```text
docs/assets/screenshots/
├── upload-flow.png
├── extraction-result.png
└── document-history.png
```

---

# Author

LogisParse Project
Patagonia · Los Lagos · Chile

---

# License

TBD by the project owner.
