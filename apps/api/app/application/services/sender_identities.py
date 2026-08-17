from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.schemas import SenderIdentityCreate
from app.domain.models import SenderIdentity


def list_sender_identities(db: Session) -> list[SenderIdentity]:
    return list(db.scalars(select(SenderIdentity).order_by(SenderIdentity.id.asc())))


def get_sender_identity(db: Session, identity_id: int) -> SenderIdentity | None:
    return db.get(SenderIdentity, identity_id)


def create_sender_identity(db: Session, payload: SenderIdentityCreate) -> SenderIdentity:
    identity = SenderIdentity(**payload.model_dump())
    db.add(identity)
    db.commit()
    db.refresh(identity)
    return identity
