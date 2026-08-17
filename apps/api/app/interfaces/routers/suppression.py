"""Suppression list router."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.dependencies import get_db
from app.application.schemas import (
    SuppressionCheckResponse,
    SuppressionEntryCreate,
    SuppressionEntryRead,
)
from app.application.services.suppression import get_suppression_entry, is_suppressed
from app.domain.models import SuppressionEntry

router = APIRouter(prefix="/suppression", tags=["suppression"])


@router.get("/check", response_model=SuppressionCheckResponse)
def check_suppression(
    email: str = Query(..., description="Email address to check"),
    db: Session = Depends(get_db),
) -> SuppressionCheckResponse:
    """Check whether an email is suppressed.

    This endpoint demonstrates the ``is_suppressed`` helper that campaign/bulk
    sending code (Phase 5+) MUST call before dispatching any message.
    """
    entry = get_suppression_entry(db, email)
    if entry:
        return SuppressionCheckResponse(
            email=email, suppressed=True, reason=entry.reason, source=entry.source
        )
    return SuppressionCheckResponse(email=email, suppressed=False, reason=None, source=None)


@router.get("", response_model=list[SuppressionEntryRead])
def list_suppressions(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[SuppressionEntryRead]:
    rows = list(
        db.scalars(
            select(SuppressionEntry)
            .order_by(SuppressionEntry.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    return [SuppressionEntryRead.model_validate(r) for r in rows]


@router.post("", response_model=SuppressionEntryRead, status_code=status.HTTP_201_CREATED)
def add_suppression(
    payload: SuppressionEntryCreate, db: Session = Depends(get_db)
) -> SuppressionEntryRead:
    normalized = str(payload.email).strip().lower()
    existing = get_suppression_entry(db, normalized)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already in the suppression list",
        )
    entry = SuppressionEntry(email=normalized, reason=payload.reason, source=payload.source)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return SuppressionEntryRead.model_validate(entry)


@router.delete("/{suppression_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_suppression(suppression_id: int, db: Session = Depends(get_db)) -> None:
    entry = db.get(SuppressionEntry, suppression_id)
    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Suppression entry not found"
        )
    db.delete(entry)
    db.commit()
