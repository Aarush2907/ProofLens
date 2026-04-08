import os

# Set before the application is imported. Settings read the environment first,
# so a developer's PostgreSQL URL in .env does not leak into these tests.
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["ENVIRONMENT"] = "test"

import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
