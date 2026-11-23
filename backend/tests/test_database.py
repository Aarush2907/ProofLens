from app.core.database import POSTGRES_CONNECT_TIMEOUT_SECONDS, engine_options


def test_memory_sqlite_uses_one_shared_connection():
    options = engine_options("sqlite+pysqlite:///:memory:")
    assert options["connect_args"]["check_same_thread"] is False
    assert options["poolclass"].__name__ == "StaticPool"


def test_file_sqlite_does_not_share_one_connection_across_requests():
    options = engine_options("sqlite+pysqlite:///prooflens.sqlite")
    assert options["connect_args"]["check_same_thread"] is False
    assert "poolclass" not in options


def test_postgres_does_not_wait_forever_for_a_down_server():
    options = engine_options("postgresql+psycopg://prooflens:prooflens@localhost:5432/prooflens")
    assert options["connect_args"]["connect_timeout"] == POSTGRES_CONNECT_TIMEOUT_SECONDS
    assert options["pool_pre_ping"] is True
