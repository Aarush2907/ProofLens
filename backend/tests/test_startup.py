from fastapi.testclient import TestClient

from app import main


def test_the_checkpointer_is_created_at_startup_not_inside_a_request(monkeypatch):
    # On PostgreSQL its setup waits for open transactions, so a request-time
    # setup would wait on the request that started the run.
    created = []
    monkeypatch.setattr(main, "get_checkpointer", lambda: created.append(True))

    with TestClient(main.app):
        assert created == [True]
