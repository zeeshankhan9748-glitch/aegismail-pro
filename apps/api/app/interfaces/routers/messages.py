from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.application.celery_client import enqueue_send_email
from app.application.dependencies import get_db
from app.application.schemas import MessageListResponse, MessageRead, MessageSendRequest
from app.application.services.messages import (
    create_message,
    get_message,
    get_message_by_idempotency_key,
    list_messages,
)
from app.application.services.sender_identities import get_sender_identity
from app.application.services.smtp_providers import get_smtp_provider

router = APIRouter(prefix="/messages", tags=["messages"])


@router.post(
    "/send",
    response_model=MessageRead,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue a one-off SMTP message",
)
def send_message(
    payload: MessageSendRequest,
    response: Response,
    db: Session = Depends(get_db),
    idempotency_key_header: str | None = Header(default=None, alias="Idempotency-Key"),
) -> MessageRead:
    provider = get_smtp_provider(db, payload.provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMTP provider not found")

    sender_identity = get_sender_identity(db, payload.sender_identity_id)
    if sender_identity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sender identity not found")
    if sender_identity.smtp_provider_id != provider.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sender identity does not belong to the selected SMTP provider",
        )

    idempotency_key = idempotency_key_header or payload.idempotency_key
    if idempotency_key:
        existing = get_message_by_idempotency_key(db, idempotency_key)
        if existing is not None:
            response.status_code = status.HTTP_200_OK
            return MessageRead.model_validate(existing)

    message = create_message(db, payload, idempotency_key)
    try:
        enqueue_send_email(message.id)
    except Exception as exc:
        message.status = "failed"
        message.error_message = "Unable to queue message for delivery"
        db.add(message)
        db.commit()
        db.refresh(message)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to queue message for delivery",
        ) from exc
    return MessageRead.model_validate(message)


@router.get("", response_model=MessageListResponse, summary="List queued and sent messages")
def list_items(
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: str | None = Query(default=None, alias="status"),
    provider_id: int | None = Query(default=None),
) -> MessageListResponse:
    return list_messages(
        db, limit=limit, offset=offset, status=status_filter, provider_id=provider_id
    )


@router.get("/{message_id}", response_model=MessageRead, summary="Get message detail by id")
def get_item(message_id: int, db: Session = Depends(get_db)) -> MessageRead:
    message = get_message(db, message_id)
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    return MessageRead.model_validate(message)
