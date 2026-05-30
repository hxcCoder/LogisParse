# Architecture

LogisParse is a **modular monolith** backend designed for simplicity and operational clarity.

## Project Structure

```
app/
├── api/v1/           # HTTP routes: auth, documents, webhooks
├── core/             # Config, database, security, middleware
├── models/           # SQLAlchemy ORM (users, documents)
├── schemas/          # Pydantic I/O contracts
├── crud/             # Data persistence helpers
└── services/         # Business logic (AI extraction, email ingestion)
```

## Key Components

- **API Layer**: FastAPI routers with JWT auth, upload validation, rate limiting
- **Services**: Business workflows (OpenAI structured extraction)
- **CRUD**: Focused database operations via SQLAlchemy async
- **Models**: User and Document tables with proper indexing
- **Core**: Configuration, async PostgreSQL connection, JWT/bcrypt security

## Simple & Fast

- No Kafka/Redis/Celery — just async Python tasks
- PostgreSQL is the source of truth
- Rate limiting and CORS configured by default
- Email ingestion is a future feature placeholder
