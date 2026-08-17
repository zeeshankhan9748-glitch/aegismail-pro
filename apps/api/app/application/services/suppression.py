"""Suppression list service.

Provides the reusable ``is_suppressed(db, email) -> bool`` helper that all
sending code paths (including future campaign/bulk-send phases) MUST call
before dispatching any message.

TODO (Phase 5 – Campaigns): When building bulk/campaign sending, import and
call ``is_suppressed`` for every recipient before enqueuing delivery.  Any
email found in ``suppression_entries`` must be silently skipped and logged
(not counted as a failure).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import SuppressionEntry


def is_suppressed(db: Session, email: str) -> bool:
    """Return True if *email* is present in the suppression list."""
    normalized = email.strip().lower()
    return (
        db.scalar(
            select(SuppressionEntry).where(SuppressionEntry.email == normalized).limit(1)
        )
        is not None
    )


def get_suppression_entry(db: Session, email: str) -> SuppressionEntry | None:
    normalized = email.strip().lower()
    return db.scalar(
        select(SuppressionEntry).where(SuppressionEntry.email == normalized)
    )
