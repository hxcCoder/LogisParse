# LogisParse - Arquitectura Visual

Este documento explica como se mueve una request por el sistema y donde vive cada responsabilidad. No describe features futuras: refleja el codigo actual.

## 1. Mapa del Sistema

```mermaid
flowchart TB
    subgraph Edge["Entrada HTTP"]
        Client["Cliente"]
        Middleware["Request ID, rate limit, CORS"]
        Routers["Routers FastAPI"]
    end

    subgraph App["Aplicacion"]
        Deps["api/deps.py<br/>settings, db, current_user"]
        Auth["auth.py<br/>register, login"]
        Documents["documents.py<br/>upload, list, get"]
        Services["services/<br/>upload validation, extractor"]
        Crud["crud/<br/>user, document"]
    end

    subgraph Data["Datos"]
        Models["models/<br/>User, Document"]
        DB[("Database")]
    end

    Client --> Middleware --> Routers
    Routers --> Auth
    Routers --> Documents
    Routers -. Depends .-> Deps
    Auth --> Crud
    Documents --> Services
    Documents --> Crud
    Crud --> Models --> DB
```

## 2. Dependency Injection

La app no crea sesiones de base de datos dentro de los handlers. El `lifespan` inicializa engine y session maker; cada request recibe sus dependencias con `Depends()`.

```mermaid
flowchart LR
    Startup["create_app lifespan"] --> Engine["build_engine(settings)"]
    Engine --> SessionMaker["build_session_maker(engine)"]
    SessionMaker --> State["app.state.session_maker"]

    Request["HTTP request"] --> Handler["Route handler"]
    Handler -.-> GetDB["get_db(request)"]
    GetDB --> State
    GetDB --> Session["AsyncSession per request"]

    Handler -.-> GetSettings["get_settings_dep()"]
    GetSettings --> Settings["Settings cached"]

    Handler -.-> CurrentUser["get_current_user()"]
    CurrentUser --> Token["decode JWT"]
    CurrentUser --> Session
```

## 3. Upload y Extraccion

```mermaid
flowchart TD
    A["POST /documents/upload"] --> B["JWT: get_current_user"]
    B --> C["read_and_validate_upload"]
    C --> D{"Archivo valido?"}
    D -- "No" --> E["HTTP 400 / 413"]
    D -- "Si" --> F["create_document<br/>PENDING"]
    F --> G["update_status<br/>PROCESSING"]
    G --> H["extract_document"]
    H --> I{"Extraccion OK?"}
    I -- "Si" --> J["update_status<br/>EXTRACTED + JSON"]
    I -- "Error controlado" --> K["update_status<br/>FAILED + error_logs"]
    I -- "Error inesperado" --> L["update_status<br/>FAILED + mensaje generico"]
    J --> M["DocumentResponse"]
    K --> M
    L --> M
```

## 4. Pipeline del Extractor

```mermaid
flowchart LR
    File["PDF / PNG / JPG"] --> Text["extract_text"]
    Text --> Source{"Tipo"}
    Source -- "PDF" --> PDF["pdfplumber"]
    Source -- "Imagen" --> OCR["Tesseract OCR"]
    PDF --> Regex["run_regex"]
    OCR --> Regex
    Regex --> Confidence{"Campos faltantes<br/>o baja confianza?"}
    Confidence -- "No" --> Schema["to_schema"]
    Confidence -- "Si" --> AI["OpenAI Structured Outputs"]
    AI --> Merge["Merge<br/>regex tiene prioridad"]
    Merge --> Result["ExtractedLogisticsData"]
    Schema --> Result
```

## 5. Estados del Documento

```mermaid
stateDiagram-v2
    [*] --> PENDING: create_document
    PENDING --> PROCESSING: upload validado
    PROCESSING --> EXTRACTED: extraccion exitosa
    PROCESSING --> FAILED: archivo invalido para extraer
    PROCESSING --> FAILED: error inesperado
    EXTRACTED --> [*]
    FAILED --> [*]
```

## 6. Modelo de Datos

```mermaid
erDiagram
    USERS ||--o{ DOCUMENTS : owns

    USERS {
        string id PK
        string email UK
        string hashed_password
        string full_name
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    DOCUMENTS {
        string id PK
        string user_id FK
        string filename
        string content_type
        enum status
        json extracted_data
        text error_logs
        datetime created_at
        datetime updated_at
    }
```

## 7. Arquitectura de Tests

```mermaid
flowchart LR
    Tests["pytest"] --> Overrides["app.dependency_overrides"]
    Overrides --> TestSettings["Settings de test"]
    Overrides --> TestDB["SQLite in-memory"]
    TestDB --> Client["TestClient"]
    TestSettings --> Client
    Client --> API["Handlers reales"]
    API --> Assertions["Assertions unit/integration"]
```

## Lectura Arquitectonica

| Decision | Valor |
| --- | --- |
| Monolito modular | Menos piezas operacionales, mas claridad para el concurso |
| DI explicita | Handlers testeables y sin sesiones globales |
| Extractor hibrido | Regex rapido primero, AI solo para completar |
| Estados persistidos | Trazabilidad de cada documento |
| Tests con overrides | Misma API, infraestructura reemplazable |

## Observaciones Reales

| Punto | Lectura |
| --- | --- |
| `upload_validation.py` usa `settings` directo | Funciona, pero no sigue al 100% el patron DI usado por los routers |
| Rate limit en memoria | Correcto para una instancia; en despliegue multi-replica requeriria almacenamiento compartido |
| AI fallback por umbral | Si regex supera el umbral, campos faltantes pueden quedar vacios por decision del pipeline |
