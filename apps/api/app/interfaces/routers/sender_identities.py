from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.application.dependencies import get_db
from app.application.schemas import SenderIdentityCreate, SenderIdentityRead
from app.application.services.sender_identities import (
    create_sender_identity,
    get_sender_identity,
    list_sender_identities,
)
from app.domain.models import SMTPProvider

router = APIRouter(prefix="/sender-identities", tags=["sender identities"])


@router.get("", response_model=list[SenderIdentityRead], summary="List sender identities")
def list_items(db: Session = Depends(get_db)) -> list[SenderIdentityRead]:
    return [SenderIdentityRead.model_validate(item) for item in list_sender_identities(db)]


@router.post(
    "",
    response_model=SenderIdentityRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create sender identity",
)
def create_item(payload: SenderIdentityCreate, db: Session = Depends(get_db)) -> SenderIdentityRead:
    if db.get(SMTPProvider, payload.smtp_provider_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMTP provider not found")
    identity = create_sender_identity(db, payload)
    return SenderIdentityRead.model_validate(identity)


@router.get(
    "/{identity_id}", response_model=SenderIdentityRead, summary="Get sender identity by id"
)
def get_item(identity_id: int, db: Session = Depends(get_db)) -> SenderIdentityRead:
    identity = get_sender_identity(db, identity_id)
    if identity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sender identity not found"
        )
    return SenderIdentityRead.model_validate(identity)
