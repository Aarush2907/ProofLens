import logging

from sqlalchemy import create_engine, inspect, text
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
        # One shared connection keeps an in-memory database visible to every
        # session. A file database must not share that connection: concurrent
        # requests then corrupt reads. PostgreSQL keeps a normal pool.
        options = {"connect_args": {"check_same_thread": False, "timeout": 5}}
        if ":memory:" in database_url:
            options["poolclass"] = StaticPool
        return options
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
    # Importing the package registers every model on Base. Importing at module
    # level would cycle: the model modules import Base from this file.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _add_missing_question_columns()


def _add_missing_question_columns() -> None:
    """Add columns introduced after the first research_questions table.

    create_all does not alter a table that already exists. Milestone 1
    databases need stage and error_message before a run can be stored.
    """

    inspector = inspect(engine)
    if "research_questions" not in inspector.get_table_names():
        return
    present = {column["name"] for column in inspector.get_columns("research_questions")}
    statements = []
    if "stage" not in present:
        statements.append(
            "ALTER TABLE research_questions ADD COLUMN stage VARCHAR(32) DEFAULT 'submitted'"
        )
    if "error_message" not in present:
        statements.append("ALTER TABLE research_questions ADD COLUMN error_message TEXT")
    for name, statement in {
        "prompt_tokens": "ALTER TABLE research_questions ADD COLUMN prompt_tokens INTEGER NOT NULL DEFAULT 0",
        "completion_tokens": "ALTER TABLE research_questions ADD COLUMN completion_tokens INTEGER NOT NULL DEFAULT 0",
        "estimated_cost_usd": "ALTER TABLE research_questions ADD COLUMN estimated_cost_usd FLOAT NOT NULL DEFAULT 0",
    }.items():
        if name not in present:
            statements.append(statement)
    statements.extend(_missing_result_columns(inspector))
    if not statements:
        return
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _missing_result_columns(inspector) -> list[str]:
    """Add source and claim columns introduced with the evidence records."""

    statements = []
    if "research_sources" in inspector.get_table_names():
        present = {column["name"] for column in inspector.get_columns("research_sources")}
        additions = {
            "domain": "ALTER TABLE research_sources ADD COLUMN domain TEXT DEFAULT ''",
            "author": "ALTER TABLE research_sources ADD COLUMN author TEXT DEFAULT ''",
            "published_on": "ALTER TABLE research_sources ADD COLUMN published_on TEXT DEFAULT ''",
            "retrieved_at": "ALTER TABLE research_sources ADD COLUMN retrieved_at TIMESTAMP",
        }
        for name, statement in additions.items():
            if name not in present:
                statements.append(statement)
    if "research_claims" in inspector.get_table_names():
        present = {column["name"] for column in inspector.get_columns("research_claims")}
        if "source_id" not in present:
            statements.append("ALTER TABLE research_claims ADD COLUMN source_id UUID")
        if "review_status" not in present:
            statements.append(
                "ALTER TABLE research_claims ADD COLUMN review_status VARCHAR(32) DEFAULT 'pending'"
            )
    return statements


def database_is_reachable() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        # A health check has to report the failure instead of crashing the API.
        # Startup still logs a full traceback when table creation itself fails.
        logger.warning("Database is not reachable: %s", exc.__class__.__name__)
        return False
