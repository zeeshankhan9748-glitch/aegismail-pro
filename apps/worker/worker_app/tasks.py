from collections import defaultdict, deque
import math
import time
from threading import Lock

from celery.exceptions import Retry
from celery.utils.log import get_task_logger

from worker_app.api_bridge import Message, SMTPProvider, SenderIdentity, SessionLocal, utcnow
from worker_app.celery_app import celery_app
from worker_app.settings import get_worker_settings

from app.application.services.smtp_delivery import (  # type: ignore[attr-defined]
    SMTP_EXCEPTIONS,
    build_smtp_error_message,
    send_smtp_message,
)

logger = get_task_logger(__name__)
settings = get_worker_settings()
_provider_windows: dict[int, deque[float]] = defaultdict(deque)
_provider_windows_lock = Lock()


def _throttle_delay_seconds(provider: SMTPProvider) -> int:
    limit = provider.throttle_limit_per_minute
    if limit <= 0:
        return 0

    now = time.monotonic()
    with _provider_windows_lock:
        window = _provider_windows[provider.id]
        while window and now - window[0] >= 60:
            window.popleft()
        if len(window) >= limit:
            return max(1, math.ceil(60 - (now - window[0])))
    return 0


def _record_provider_send(provider_id: int) -> None:
    now = time.monotonic()
    with _provider_windows_lock:
        _provider_windows[provider_id].append(now)


@celery_app.task(bind=True, max_retries=settings.smtp_max_send_attempts)
def send_email_task(self, message_id: int) -> dict[str, str | int]:
    session = SessionLocal()
    try:
        message = session.get(Message, message_id)
        if message is None:
            logger.warning("message missing", extra={"message_id": message_id})
            return {"status": "missing", "message_id": message_id}

        provider = session.get(SMTPProvider, message.provider_id)
        sender_identity = session.get(SenderIdentity, message.sender_identity_id)
        if provider is None or sender_identity is None:
            message.status = "failed"
            message.attempt_count += 1
            message.error_message = "SMTP provider or sender identity is missing"
            session.add(message)
            session.commit()
            return {"status": "failed", "message_id": message_id}

        throttle_delay = _throttle_delay_seconds(provider)
        if throttle_delay:
            message.status = "deferred"
            message.error_message = "Provider throttle limit reached; retry scheduled"
            session.add(message)
            session.commit()
            raise self.retry(countdown=throttle_delay)

        message.status = "processing"
        message.error_message = None
        session.add(message)
        session.commit()

        try:
            send_smtp_message(
                provider,
                sender_identity,
                message,
                timeout=settings.smtp_connect_timeout_seconds,
            )
        except SMTP_EXCEPTIONS as exc:
            message.attempt_count += 1
            message.error_message = build_smtp_error_message(exc)
            if message.attempt_count >= settings.smtp_max_send_attempts:
                message.status = "failed"
                session.add(message)
                session.commit()
                return {"status": "failed", "message_id": message_id, "attempt_count": message.attempt_count}

            message.status = "deferred"
            session.add(message)
            session.commit()
            raise self.retry(exc=exc, countdown=min(300, 2 ** message.attempt_count))

        message.status = "sent"
        message.error_message = None
        message.sent_at = utcnow()
        _record_provider_send(provider.id)
        session.add(message)
        session.commit()
        return {"status": "sent", "message_id": message_id, "attempt_count": message.attempt_count}
    except Retry:
        raise
    finally:
        session.close()


@celery_app.task
def ping_task() -> dict[str, str]:
    return {"status": "ok", "message": "worker reachable"}
