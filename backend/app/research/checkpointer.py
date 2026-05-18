import sqlite3

from app.core.config import get_settings

_saver = None
_connection = None


def get_checkpointer():
    """Return the process-wide LangGraph checkpointer.

    The thread id is the research question id, so two sessions never resume
    each other's state. SQLite tests keep this in memory for the process.
    PostgreSQL keeps it in the same database the rest of the app uses, so a
    restarted API can resume a review that was already waiting.
    """

    global _saver, _connection
    if _saver is not None:
        return _saver

    url = get_settings().database_url
    if url.startswith("sqlite"):
        from langgraph.checkpoint.sqlite import SqliteSaver

        _connection = sqlite3.connect(":memory:", check_same_thread=False)
        _saver = SqliteSaver(_connection)
        _saver.setup()
        return _saver

    import psycopg
    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg.rows import dict_row

    postgres_url = url.replace("postgresql+psycopg://", "postgresql://", 1)
    _connection = psycopg.connect(
        postgres_url,
        autocommit=True,
        prepare_threshold=0,
        row_factory=dict_row,
    )
    _saver = PostgresSaver(_connection)
    _saver.setup()
    return _saver
