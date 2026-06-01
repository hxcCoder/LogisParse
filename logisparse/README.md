# LogisParse

Backend FastAPI para automatizar la lectura de documentos logisticos: recibe PDFs o imagenes, valida el archivo, extrae datos de despacho y guarda el resultado estructurado por usuario.

El proyecto esta pensado como un monolito modular: simple de ejecutar, facil de testear y con dependencias explicitas.

## Vista Rapida

```mermaid
flowchart LR
    Client["Cliente / integracion"] --> API["FastAPI API"]
    API --> Auth["Auth JWT"]
    API --> Docs["Documentos"]
    Docs --> Validate["Validacion de upload"]
    Validate --> Extract["OCR + Regex + AI fallback"]
    Extract --> DB[("PostgreSQL / SQLite tests")]
    Auth --> DB
```

## Que Resuelve

- Registra y autentica usuarios con JWT.
- Recibe documentos logisticos en PDF, PNG o JPG.
- Valida extension, contenido real y tamano.
- Extrae origen, destino, patente, chofer, fecha, numero de guia e items.
- Persiste documentos con estado `PENDING`, `PROCESSING`, `EXTRACTED` o `FAILED`.
- Permite tests aislados mediante overrides de dependencias de FastAPI.

## Stack

| Capa | Tecnologia |
| --- | --- |
| API | FastAPI |
| Datos | SQLAlchemy 2.0 async |
| DB prod | PostgreSQL |
| DB tests | SQLite en memoria |
| Auth | JWT + Argon2 |
| Extraccion | pdfplumber, Tesseract, regex, OpenAI Structured Outputs |
| Tests | pytest |

## Flujo Principal

```mermaid
sequenceDiagram
    participant U as Usuario
    participant API as FastAPI
    participant V as Upload validation
    participant X as Extractor
    participant DB as Database

    U->>API: POST /api/v1/documents/upload
    API->>API: get_current_user()
    API->>V: read_and_validate_upload(file)
    V-->>API: filename, content_type, bytes
    API->>DB: create_document(PENDING)
    API->>DB: update_status(PROCESSING)
    API->>X: extract_document(bytes, type, settings)
    X-->>API: ExtractedLogisticsData
    API->>DB: update_status(EXTRACTED, extracted_data)
    API-->>U: DocumentResponse
```

## Estructura

```text
app/
  api/
    deps.py          # Dependency injection: settings, DB session, current user
    v1/              # Routers de auth y documentos
  core/              # Config, database, security, middleware, logging
  crud/              # Operaciones de persistencia
  models/            # Modelos SQLAlchemy
  schemas/           # Contratos Pydantic
  services/          # Validacion de uploads y extraccion documental
tests/               # Unit e integration tests con overrides
migrations/          # Alembic
docs/                # Notas tecnicas cortas
```

## Endpoints

| Metodo | Ruta | Uso |
| --- | --- | --- |
| `POST` | `/api/v1/auth/register` | Crear usuario |
| `POST` | `/api/v1/auth/login` | Obtener token JWT |
| `POST` | `/api/v1/documents/upload` | Subir y procesar documento |
| `GET` | `/api/v1/documents` | Listar documentos del usuario |
| `GET` | `/api/v1/documents/{document_id}` | Ver un documento |
| `GET` | `/health` | Health check |
| `GET` | `/ready` | Readiness check |

## Puesta en Marcha

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

Crear `.env` a partir de `.env.example` y configurar:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/logisparse_db
SECRET_KEY=change-me-with-a-long-random-secret
OPENAI_API_KEY=sk-...
DEBUG=true
```

Ejecutar:

```bash
uvicorn app.main:app --reload
pytest
```

## Documentacion Visual

- [ARCHITECTURE.md](ARCHITECTURE.md): mapa visual del sistema, DI, estados y modelo de datos.
- [docs/AI_EXTRACTION.md](docs/AI_EXTRACTION.md): flujo de extraccion documental.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md): resumen corto para orientarse rapido.
