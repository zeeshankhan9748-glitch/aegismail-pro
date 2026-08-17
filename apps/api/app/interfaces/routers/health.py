from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.application.dependencies import get_db
from app.application.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
def healthcheck() -> HealthResponse:
    return HealthResponse(status="ok", detail="AegisMail Pro API is alive")


@router.get("/ready", response_model=HealthResponse, summary="Readiness probe")
def readiness(db: Session = Depends(get_db)) -> HealthResponse:
    db.execute(text("SELECT 1"))
    return HealthResponse(status="ok", detail="Database connectivity check succeeded")
