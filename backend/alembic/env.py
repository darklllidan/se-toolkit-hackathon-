import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.config import settings

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata is only needed for `alembic revision --autogenerate`.
# Running migrations does not require it, and importing models here causes
# SQLAlchemy to register their Enum types globally — which then conflicts with
# the explicit CREATE TYPE statements in the migration scripts.
target_metadata = None


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    # target_metadata=None here: prevents SQLAlchemy from auto-emitting
    # CREATE TYPE for Enum columns defined in models (they're created
    # explicitly in the migration scripts instead).
    # target_metadata is only needed for `alembic revision --autogenerate`.
    #
    # transaction_per_migration=True ensures each migration runs and commits
    # in its own transaction, which is required for migrations that use
    # ALTER TYPE ... ADD VALUE followed by migrations that INSERT those values
    # (PostgreSQL requires the enum addition to be committed first).
    context.configure(
        connection=connection,
        target_metadata=None,
        transaction_per_migration=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        # Disable asyncpg prepared-statement cache so newly added enum values
        # are visible immediately in subsequent migrations (same connection).
        connect_args={"prepared_statement_cache_size": 0},
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
