import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import auth, documents
from app.core.config import get_settings
from app.core.database import build_engine, build_session_maker
from app.core.logging import configure_logging
from app.core.middleware import (
    InMemoryRateLimitMiddleware,
    RequestContextMiddleware,
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    The app is created with a proper lifespan context that:
    - Initializes database engine and session factory on startup
    - Stores them in app.state for dependency injection
    - Properly disposes resources on shutdown
    """
    # Load settings once during app creation
    settings = get_settings()

    configure_logging(settings.LOG_LEVEL)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        """Manage application lifecycle.

        Startup:
        - Create database engine
        - Create session factory
        - Store in app.state for dependency injection

        Shutdown:
        - Dispose database engine
        - Clean up resources
        """
        logger.info("Starting %s %s", settings.APP_TITLE, settings.APP_VERSION)

        # Initialize database during startup
        engine = build_engine(settings)
        session_maker = build_session_maker(engine)

        # Store in app.state for dependency injection
        app.state.engine = engine
        app.state.session_maker = session_maker

        logger.info("Database initialized: %s", settings.DATABASE_URL)

        yield

        # Cleanup on shutdown
        logger.info("Shutting down application")
        await engine.dispose()
        logger.info("Application shutdown complete")

    app = FastAPI(
        title=settings.APP_TITLE,
        description="Document automation API for logistics operations.",
        version=settings.APP_VERSION,
        openapi_url="/api/openapi.json" if settings.DEBUG else None,
        docs_url="/api/docs" if settings.DEBUG else None,
        redoc_url="/api/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # Add middleware (El orden es importante en FastAPI)
    app.add_middleware(InMemoryRateLimitMiddleware)
    app.add_middleware(RequestContextMiddleware)

    # --- CORRECCIÓN DE CORS AQUÍ ---
    # Unimos el localhost:3000 fijo con lo que sea que traigas en tus settings
    allowed_origins = list(set(["http://localhost:3000", "http://127.0.0.1:3000"] + settings.ALLOWED_ORIGINS))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],  # Modificado para aceptar todos los métodos (PUT, DELETE, etc.)
        allow_headers=["*"],  # Modificado para aceptar cualquier header de React/Axios
    )

    # Include routers
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    # Health check endpoints
    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": settings.APP_VERSION}

    @app.get("/ready")
    async def ready() -> dict[str, str]:
        return {"status": "ready"}

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "name": settings.APP_TITLE,
            "docs": "/api/docs",
            "health": "/health",
        }

    return app


app = create_app()