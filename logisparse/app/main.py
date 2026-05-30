import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import auth, documents
from app.core.config import get_settings
from app.core.database import close_db, init_db
from app.core.logging import configure_logging
from app.core.middleware import (
    InMemoryRateLimitMiddleware,
    RequestContextMiddleware,
)

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()  

    configure_logging(settings.LOG_LEVEL)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Starting %s %s", settings.APP_TITLE, settings.APP_VERSION)
        await init_db()
        yield
        await close_db()
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

    app.add_middleware(InMemoryRateLimitMiddleware)
    app.add_middleware(RequestContextMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": settings.APP_VERSION}

    @app.get("/ready")
    async def ready():
        return {"status": "ready"}

    @app.get("/")
    async def root():
        return {
            "name": settings.APP_TITLE,
            "docs": "/api/docs",
            "health": "/health",
        }

    return app


app = create_app()