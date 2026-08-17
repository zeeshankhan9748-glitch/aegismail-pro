from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.dependencies import get_db
from app.application.schemas import (
    SMTPConnectionTestResponse,
    SMTPProviderCreate,
    SMTPProviderRead,
    SMTPProviderUpdate,
)
from app.application.services.smtp_delivery import test_smtp_connection
from app.application.services.smtp_providers import (
    create_smtp_provider,
    get_smtp_provider,
    list_smtp_providers,
    update_smtp_provider,
)
from app.settings import get_settings

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


@router.put(
    "/{provider_id}",
    response_model=SMTPProviderRead,
    summary="Update SMTP provider",
)
def update_item(
    provider_id: int, payload: SMTPProviderUpdate, db: Session = Depends(get_db)
) -> SMTPProviderRead:
    provider = get_smtp_provider(db, provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMTP provider not found")
    try:
        provider = update_smtp_provider(db, provider, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A database constraint was violated while updating the SMTP provider",
        ) from exc
    return SMTPProviderRead.model_validate(provider)


@router.post(
    "/{provider_id}/test-connection",
    response_model=SMTPConnectionTestResponse,
    summary="Test SMTP connection",
)
def test_connection(provider_id: int, db: Session = Depends(get_db)) -> SMTPConnectionTestResponse:
    provider = get_smtp_provider(db, provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMTP provider not found")
    success, message = test_smtp_connection(
        provider, timeout=get_settings().smtp_connect_timeout_seconds
    )
    return SMTPConnectionTestResponse(success=success, provider_id=provider.id, message=message)
