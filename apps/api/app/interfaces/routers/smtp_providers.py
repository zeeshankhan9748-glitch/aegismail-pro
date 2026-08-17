from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.dependencies import get_db
from app.application.schemas import SMTPProviderCreate, SMTPProviderRead
from app.application.services.smtp_providers import (
    create_smtp_provider,
    get_smtp_provider,
    list_smtp_providers,
)

router = APIRouter(prefix="/smtp-providers", tags=["smtp providers"])


@router.get("", response_model=list[SMTPProviderRead], summary="List SMTP providers")
def list_items(db: Session = Depends(get_db)) -> list[SMTPProviderRead]:
    return [SMTPProviderRead.model_validate(item) for item in list_smtp_providers(db)]


@router.post(
    "",
    response_model=SMTPProviderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create SMTP provider",
)
def create_item(payload: SMTPProviderCreate, db: Session = Depends(get_db)) -> SMTPProviderRead:
    try:
        provider = create_smtp_provider(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A database constraint was violated while creating the SMTP provider",
        ) from exc
    return SMTPProviderRead.model_validate(provider)


@router.get("/{provider_id}", response_model=SMTPProviderRead, summary="Get SMTP provider by id")
def get_item(provider_id: int, db: Session = Depends(get_db)) -> SMTPProviderRead:
    provider = get_smtp_provider(db, provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMTP provider not found")
    return SMTPProviderRead.model_validate(provider)


@router.post("/{provider_id}/test-connection", summary="Stub SMTP connection test")
def test_connection(provider_id: int, db: Session = Depends(get_db)) -> dict[str, str | int]:
    provider = get_smtp_provider(db, provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMTP provider not found")
    return {
        "status": "not_implemented",
        "provider_id": provider.id,
        "message": "SMTP connection testing will be implemented in Phase 2.",
    }
