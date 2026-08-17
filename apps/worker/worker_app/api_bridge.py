from pathlib import Path
import sys

API_APP_PATH = Path(__file__).resolve().parents[2] / "api"
if str(API_APP_PATH) not in sys.path:
    sys.path.insert(0, str(API_APP_PATH))

from app.application.security import decrypt_secret  # noqa: E402
from app.domain.models import (  # noqa: E402
    Contact,
    ContactList,
    ContactListMember,
    ImportJob,
    Message,
    SMTPProvider,
    SenderIdentity,
    SuppressionEntry,
    utcnow,
)
from app.infrastructure.database import SessionLocal  # noqa: E402
