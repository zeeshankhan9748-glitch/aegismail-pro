from collections import defaultdict, deque
import csv
import io
import math
import re
import time
from threading import Lock

from celery.exceptions import Retry
from celery.utils.log import get_task_logger

from worker_app.api_bridge import (
    Contact,
    ContactListMember,
    ImportJob,
    Message,
    SMTPProvider,
    SenderIdentity,
    SessionLocal,
    SuppressionEntry,
    utcnow,
)
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


# ---------------------------------------------------------------------------
# Phase 4: CSV Import task
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_CANONICAL_FIELDS = {"email", "first_name", "last_name"}
_MAX_ROWS = 50_000
_BATCH_SIZE = 100


def _validate_email(value: str) -> bool:
    return bool(_EMAIL_RE.match(value.strip()))


@celery_app.task(name="worker_app.tasks.process_import_job")
def process_import_job(job_id: int) -> dict:
    """Parse and import contacts from a stored CSV.

    Algorithm:
    1. Load the ImportJob row and mark it as ``processing``.
    2. Parse the CSV using Python's stdlib ``csv`` module.
    3. For each row:
       - Validate the email address; skip + record error if invalid.
       - Check the suppression list; skip (not an error) if suppressed.
       - Upsert the contact by email.
       - Optionally add to the target contact list.
    4. Commit in batches of 100 for live progress visibility.
    5. Mark job as ``completed`` (or ``failed`` on unexpected exception).
    """
    session = SessionLocal()
    try:
        job = session.get(ImportJob, job_id)
        if job is None:
            logger.warning("import job not found", extra={"job_id": job_id})
            return {"status": "missing", "job_id": job_id}

        job.status = "processing"
        session.commit()

        csv_text = job.csv_data or ""
        mapping: dict = job.column_mapping or {}
        contact_list_id = job.contact_list_id
        error_report: list[dict] = []

        reader = csv.DictReader(io.StringIO(csv_text))
        headers = reader.fieldnames or []

        # Build reverse mapping: csv_header -> canonical_field
        # e.g. {"Email Address": "email", "First Name": "first_name"}
        reverse_map: dict[str, str] = {}
        if mapping:
            for canonical, csv_col in mapping.items():
                if csv_col in headers:
                    reverse_map[csv_col] = canonical
        else:
            # No explicit mapping: use header names directly as field names
            for h in headers:
                reverse_map[h] = h

        # Verify email field is reachable
        email_csv_col = None
        for csv_col, canon in reverse_map.items():
            if canon == "email":
                email_csv_col = csv_col
                break
        if email_csv_col is None and "email" in headers:
            email_csv_col = "email"
            reverse_map["email"] = "email"

        rows_list = list(reader)
        total = min(len(rows_list), _MAX_ROWS)
        job.total_rows = total
        session.commit()

        imported = 0
        skipped = 0
        errors = 0
        processed = 0

        for row_index, row in enumerate(rows_list[:_MAX_ROWS], start=1):
            # Extract email
            raw_email = ""
            if email_csv_col:
                raw_email = (row.get(email_csv_col) or "").strip()
            else:
                # Fallback: look for a column whose header contains "email"
                for k, v in row.items():
                    if "email" in (k or "").lower():
                        raw_email = (v or "").strip()
                        break

            if not raw_email:
                error_report.append({"row": row_index, "error": "Missing email address"})
                errors += 1
                processed += 1
                if processed % _BATCH_SIZE == 0:
                    job.processed_rows = processed
                    job.imported_count = imported
                    job.skipped_count = skipped
                    job.error_count = errors
                    job.error_report = error_report
                    session.commit()
                continue

            if not _validate_email(raw_email):
                error_report.append({"row": row_index, "error": f"Invalid email: {raw_email}"})
                errors += 1
                processed += 1
                if processed % _BATCH_SIZE == 0:
                    job.processed_rows = processed
                    job.imported_count = imported
                    job.skipped_count = skipped
                    job.error_count = errors
                    job.error_report = error_report
                    session.commit()
                continue

            normalized_email = raw_email.lower()

            # Check suppression list
            suppressed = session.scalar(
                __import__("sqlalchemy").select(SuppressionEntry).where(
                    SuppressionEntry.email == normalized_email
                ).limit(1)
            )
            if suppressed is not None:
                skipped += 1
                processed += 1
                if processed % _BATCH_SIZE == 0:
                    job.processed_rows = processed
                    job.imported_count = imported
                    job.skipped_count = skipped
                    job.error_count = errors
                    job.error_report = error_report
                    session.commit()
                continue

            # Extract other canonical fields
            first_name: str | None = None
            last_name: str | None = None
            custom_fields: dict = {}

            for csv_col, canon in reverse_map.items():
                if canon == "email":
                    continue
                val = (row.get(csv_col) or "").strip() or None
                if canon == "first_name":
                    first_name = val
                elif canon == "last_name":
                    last_name = val
                elif val is not None:
                    custom_fields[canon] = val

            # Upsert contact
            from sqlalchemy import select as sa_select

            contact = session.scalar(
                sa_select(Contact).where(Contact.email == normalized_email)
            )
            if contact is None:
                contact = Contact(
                    email=normalized_email,
                    first_name=first_name,
                    last_name=last_name,
                    custom_fields=custom_fields or None,
                    status="active",
                )
                session.add(contact)
                session.flush()
            else:
                if first_name:
                    contact.first_name = first_name
                if last_name:
                    contact.last_name = last_name
                if custom_fields:
                    contact.custom_fields = {**(contact.custom_fields or {}), **custom_fields}
                session.flush()

            # Add to target list if given
            if contact_list_id is not None:
                existing_membership = session.scalar(
                    sa_select(ContactListMember).where(
                        ContactListMember.contact_list_id == contact_list_id,
                        ContactListMember.contact_id == contact.id,
                    )
                )
                if existing_membership is None:
                    session.add(
                        ContactListMember(
                            contact_list_id=contact_list_id,
                            contact_id=contact.id,
                        )
                    )

            imported += 1
            processed += 1

            if processed % _BATCH_SIZE == 0:
                job.processed_rows = processed
                job.imported_count = imported
                job.skipped_count = skipped
                job.error_count = errors
                job.error_report = error_report
                session.commit()

        # Final update
        job.processed_rows = processed
        job.imported_count = imported
        job.skipped_count = skipped
        job.error_count = errors
        job.error_report = error_report if error_report else None
        job.status = "completed"
        job.completed_at = utcnow()
        session.commit()
        return {
            "status": "completed",
            "job_id": job_id,
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
        }

    except Exception as exc:
        logger.exception("import job failed", extra={"job_id": job_id, "error": str(exc)})
        try:
            job = session.get(ImportJob, job_id)
            if job:
                job.status = "failed"
                job.completed_at = utcnow()
                session.commit()
        except Exception:
            pass
        return {"status": "failed", "job_id": job_id, "error": str(exc)}
    finally:
        session.close()

