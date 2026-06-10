# LogisParse

Verificacion documental inteligente para PDFs tributarios y logisticos chilenos.

LogisParse reduce trabajo manual en documentos del SII y operaciones logisticas:
recibe PDFs o imagenes, extrae texto, detecta estructura, normaliza datos,
valida consistencia y deja un resultado revisable por una persona.

El foco del proyecto es claro: IA hibrida, pocos tokens, trazabilidad y una
arquitectura simple para presentar y mantener.

## Flujo del Sistema

```mermaid
flowchart LR
    User["Operador documental"] --> UI["Next.js + Tailwind"]
    UI --> API["FastAPI"]
    API --> Auth["JWT simple"]
    API --> Upload["Validacion de archivo"]
    Upload --> Extract["Pipeline documental"]
    Extract --> DB[("PostgreSQL")]
    DB --> Review["Resultado para revision humana"]
    Review --> User
```

## Pipeline Documental

```mermaid
flowchart TD
    A["PDF / PNG / JPG"] --> B["Validar extension, bytes y peso"]
    B --> C["Extraer texto local"]
    C --> D["Regex y parsing deterministico"]
    D --> E["Normalizar estructura"]
    E --> F{"Faltan campos<br/>o baja confianza?"}
    F -- "No" --> G["Guardar resultado"]
    F -- "Si" --> H["Seleccionar fragmentos relevantes"]
    H --> I["IA como verificador parcial"]
    I --> J["Merge: regex tiene prioridad"]
    J --> G
    G --> K["Revision humana"]
```

La IA no recibe documentos completos. Solo viajan fragmentos asociados a campos
faltantes o inconsistentes. Esto baja costo, mejora privacidad y hace que el
comportamiento sea mas explicable.

## Que Extrae

- Origen y destino.
- Patente del camion.
- Chofer o conductor.
- Fecha de despacho.
- Numero de guia o folio.
- Items logisticos detectados.
- Observaciones para revision.

## Arquitectura Simplificada

```text
app/
  api/
    deps.py              # settings, db session, current user
    v1/
      auth.py            # registro y login JWT
      documents.py       # upload, listado y detalle
  core/                  # config, database, security, middleware
  crud/                  # SQLAlchemy directo, sin repositorios abstractos
  models/                # User, Document
  schemas/               # Pydantic contracts
  services/
    upload_validation.py # validacion de archivos
    document_extractor.py# texto, regex, IA parcial
frontend/                # Next.js + Tailwind conectable al API
tests/                   # unit + integration
migrations/              # Alembic
docs/                    # guias tecnicas cortas
```

## Decisiones Tecnicas

| Decision | Motivo |
| --- | --- |
| Monolito FastAPI | Menos piezas, demo clara, despliegue simple |
| PostgreSQL + SQLAlchemy async | Persistencia robusta sin complejidad enterprise |
| JWT simple | Suficiente para MVP y demo autenticada |
| Regex primero | Rapido, barato y explicable |
| IA solo fallback | Menos tokens y menos dependencia externa |
| Estados documentales | Trazabilidad: `PENDING`, `PROCESSING`, `EXTRACTED`, `FAILED` |
| Tests con overrides | API real, DB en memoria y sin tocar PostgreSQL |

## Endpoints

| Metodo | Ruta | Uso |
| --- | --- | --- |
| `POST` | `/api/v1/auth/register` | Crear usuario |
| `POST` | `/api/v1/auth/login` | Obtener JWT |
| `POST` | `/api/v1/documents/upload` | Subir y procesar documento |
| `GET` | `/api/v1/documents` | Listar documentos del usuario |
| `GET` | `/api/v1/documents/{document_id}` | Ver detalle |
| `GET` | `/health` | Health check |
| `GET` | `/ready` | Readiness check |

## Puesta en Marcha

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Crear `.env` desde `.env.example`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/logisparse_db
SECRET_KEY=change-me-with-a-long-random-secret
OPENAI_API_KEY=sk-...
DEBUG=true
```

Ejecutar API:

```bash
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Ejecutar tests:

```bash
.venv\Scripts\python.exe -m pytest --cov=app --cov-report=term-missing
```

## Frontend

Hay un scaffold listo en `frontend/` con Next.js + Tailwind.

```bash
cd frontend
npm.cmd install
npm.cmd run dev
```

Configurar:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Guia de conexion: [docs/FRONTEND_GUIDE.md](docs/FRONTEND_GUIDE.md).

## Testing

La suite cubre:

- Auth y JWT.
- CRUD documental.
- Validacion de extension, contenido real y tamano.
- Pipeline de extractor con regex, umbral de confianza y fallback IA.
- Rutas principales con DB SQLite en memoria.
- Casos de error esperados y acceso entre usuarios.

Cobertura verificada: 92%.

## Seguridad Basica

- Passwords con Argon2.
- JWT firmado con expiracion.
- Validacion de bytes reales del archivo.
- Limite de tamano de upload.
- CORS configurable.
- Rate limit en memoria para MVP.
- No se envian documentos completos a IA.

## Enfoque Concurso INACAP

LogisParse se explica en una frase:

> Convierte revision manual de documentos logisticos/SII en un flujo asistido,
> trazable y barato, donde la IA ayuda solo cuando las reglas locales no bastan.

Para jurado no tecnico: reduce digitacion y errores humanos.
Para jurado tecnico: muestra parsing local, IA acotada, contratos Pydantic,
persistencia async, tests y arquitectura mantenible.

## Roadmap v2

- Endpoint de revision humana y correccion final.
- Historial de cambios por campo.
- Mejor OCR para documentos escaneados.
- Validaciones especificas SII por tipo de DTE.
- Exportacion CSV/Excel para operacion.
- Almacenamiento privado de archivos originales.

## Documentacion

- [ARCHITECTURE.md](ARCHITECTURE.md): diagnostico, refactor y arquitectura objetivo.
- [docs/AI_EXTRACTION.md](docs/AI_EXTRACTION.md): detalle del pipeline hibrido.
- [docs/FRONTEND_GUIDE.md](docs/FRONTEND_GUIDE.md): conexion Next.js + Tailwind.
