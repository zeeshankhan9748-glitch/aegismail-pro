from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.application.schemas import MessageListResponse, MessageSendRequest, MessageSummary
from app.domain.models import Message


def get_message_by_idempotency_key(db: Session, idempotency_key: str) -> Message | None:
    return db.scalar(select(Message).where(Message.idempotency_key == idempotency_key))


def create_message(
    db: Session, payload: MessageSendRequest, idempotency_key: str | None
) -> Message:
    message = Message(
        provider_id=payload.provider_id,
        sender_identity_id=payload.sender_identity_id,
        recipient_email=str(payload.recipient_email),
        subject=payload.subject or "",
        body_text=payload.body_text or "",
        body_html=payload.body_html,
        status="queued",
        idempotency_key=idempotency_key,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_message(db: Session, message_id: int) -> Message | None:
    return db.get(Message, message_id)


def list_messages(
    db: Session,
    *,
    limit: int,
    offset: int,
    status: str | None,
    provider_id: int | None,
) -> MessageListResponse:
    filters = []
    if status:
        filters.append(Message.status == status)
    if provider_id is not None:
        filters.append(Message.provider_id == provider_id)

    base_query = select(Message).options(
        joinedload(Message.provider), joinedload(Message.sender_identity)
    )
    count_query = select(func.count()).select_from(Message)
    if filters:
        base_query = base_query.where(*filters)
        count_query = count_query.where(*filters)

    rows = list(
        db.scalars(base_query.order_by(Message.created_at.desc()).limit(limit).offset(offset))
    )
    total = db.scalar(count_query) or 0

    return MessageListResponse(
        items=[
            MessageSummary(
                id=row.id,
                provider_id=row.provider_id,
                sender_identity_id=row.sender_identity_id,
                provider_name=row.provider.name,
                sender_display_name=row.sender_identity.display_name,
                recipient_email=row.recipient_email,
                subject=row.subject,
                status=row.status,
                error_message=row.error_message,
                attempt_count=row.attempt_count,
                created_at=row.created_at,
                updated_at=row.updated_at,
                sent_at=row.sent_at,
            )
            for row in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )
