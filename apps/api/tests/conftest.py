import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB_PATH = Path(__file__).parent / "test.db"
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{TEST_DB_PATH}"
os.environ["JWT_SECRET"] = "test-secret-with-sufficient-length-123456"
os.environ["APP_ENCRYPTION_KEY"] = "zBCLvKftVYqfN2UhcJqj7A29qa0mWdddwG4QzaHm9yY="
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

from app.domain.models import (  # noqa: F401
    APIKey,
    Contact,
    ContactList,
    ContactListMember,
    ImportJob,
    Message,
    Role,
    SenderIdentity,
    SMTPProvider,
    SuppressionEntry,
    Template,
    TemplateVersion,
    User,
)
from app.infrastructure.database import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
