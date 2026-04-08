import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# A missing PostgreSQL server should fail the health check, not freeze startup.
POSTGRES_CONNECT_TIMEOUT_SECONDS = 3


class Base(DeclarativeBase):
    pass


def engine_options(database_url: str) -> dict:
    if database_url.startswith("sqlite"):
        # StaticPool keeps an in-memory SQLite database on one connection.
        # Tests use that. PostgreSQL keeps a normal connection pool.
        return {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }
    return {
        "pool_pre_ping": True,
        "connect_args": {"connect_timeout": POSTGRES_CONNECT_TIMEOUT_SECONDS},
    }


def build_engine(database_url: str):
    return create_engine(database_url, **engine_options(database_url))


engine = build_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_database() -> None:
    # Importing the model registers it on Base. Importing at module level
    # would cycle: the model module imports Base from this file.
    from app.models import research_question  # noqa: F401

    Base.metadata.create_all(bind=engine)


def database_is_reachable() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        # A health check has to report the failure instead of crashing the API.
        # Startup still logs a full traceback when table creation itself fails.
        logger.warning("Database is not reachable: %s", exc)
        return False
