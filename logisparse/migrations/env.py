import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config, create_async_engine

from alembic import context

# Agregar el directorio raíz al path para poder importar app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.models import Base

# Configurar logging
if context.config.config_file_name is not None:
    fileConfig(context.config.config_file_name)

# Configurar la URL de la base de datos
config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Ejecutar migraciones en modo offline."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Ejecutar migraciones con una conexión dada."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Ejecutar migraciones en modo asíncrono con NullPool."""
    # Crear el engine con NullPool y statement_cache_size=0
    engine = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,  # <-- Cada conexión es nueva
        connect_args={"statement_cache_size": 0},  # <-- Deshabilitar prepared statements
        echo=False,
    )

    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await engine.dispose()


def run_migrations_online() -> None:
    """Ejecutar migraciones en modo online."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()