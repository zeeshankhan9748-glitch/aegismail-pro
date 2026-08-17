import os
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[3]
API_APP_PATH = ROOT_DIR / "apps" / "api"
if str(API_APP_PATH) not in sys.path:
    sys.path.insert(0, str(API_APP_PATH))

TEST_DB_PATH = Path(__file__).parent / "test_worker.db"
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{TEST_DB_PATH}"
os.environ["JWT_SECRET"] = "test-secret-with-sufficient-length-123456"
os.environ["APP_ENCRYPTION_KEY"] = "zBCLvKftVYqfN2UhcJqj7A29qa0mWdddwG4QzaHm9yY="
os.environ.setdefault("SMTP_MAX_SEND_ATTEMPTS", "5")

from app.domain.models import Message, Role, SenderIdentity, SMTPProvider, User  # noqa: F401,E402
from app.infrastructure.database import Base, engine  # noqa: E402


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
