"""Import Jobs router — CSV contact import with background Celery processing."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.celery_client import celery_client
from app.application.dependencies import get_db
from app.application.schemas import ImportJobRead
from app.domain.models import ContactList, ImportJob

router = APIRouter(prefix="/import-jobs", tags=["import-jobs"])

# Server-side limits (enforced before enqueuing the Celery task)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_ROWS = 50_000


@router.post("", response_model=ImportJobRead, status_code=status.HTTP_202_ACCEPTED)
async def create_import_job(
    file: UploadFile = File(..., description="CSV file to import"),
    contact_list_id: int | None = Form(default=None),
    column_mapping: str | None = Form(
        default=None,
        description=(
            'JSON string mapping canonical field names to CSV column headers, e.g. '
            '{"email": "Email Address", "first_name": "First Name"}'
        ),
    ),
    db: Session = Depends(get_db),
) -> ImportJobRead:
    """Accept a CSV file upload, create an import job, enqueue processing.

    Returns 202 immediately with the job id.  Poll ``GET /import-jobs/{id}``
    for live progress.

    The *column_mapping* form field should be a JSON object whose keys are
    canonical field names (``email``, ``first_name``, ``last_name``; anything
    else goes into ``custom_fields``) and whose values are the matching header
    strings found in the CSV file.  If omitted, the worker will use the CSV
    header row directly as field names.
    """
    # Validate contact list exists if provided
    if contact_list_id is not None:
        cl = db.get(ContactList, contact_list_id)
        if cl is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Contact list not found"
            )

    # Read and validate file
    raw = await file.read()
    if len(raw) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // 1_048_576} MB"
            ),
        )

    # Quick row count (count newlines as a fast heuristic; exact count done in worker)
    estimated_rows = raw.count(b"\n")
    if estimated_rows > MAX_ROWS + 1:  # +1 for header
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum row limit of {MAX_ROWS:,} rows",
        )

    try:
        csv_text = raw.decode("utf-8-sig")  # strip BOM if present
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file must be UTF-8 encoded",
        )

    # Parse column_mapping JSON if provided
    mapping: dict | None = None
    if column_mapping:
        import json

        try:
            mapping = json.loads(column_mapping)
            if not isinstance(mapping, dict):
                raise ValueError("column_mapping must be a JSON object")
        except (json.JSONDecodeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid column_mapping: {exc}",
            )

    job = ImportJob(
        filename=file.filename or "upload.csv",
        status="pending",
        contact_list_id=contact_list_id,
        csv_data=csv_text,
        column_mapping=mapping,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Enqueue the Celery task
    celery_client.send_task("worker_app.tasks.process_import_job", args=[job.id])

    return ImportJobRead.model_validate(job)


@router.get("", response_model=list[ImportJobRead])
def list_import_jobs(
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[ImportJobRead]:
    rows = list(
        db.scalars(
            select(ImportJob)
            .order_by(ImportJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    return [ImportJobRead.model_validate(r) for r in rows]


@router.get("/{job_id}", response_model=ImportJobRead)
def get_import_job(job_id: int, db: Session = Depends(get_db)) -> ImportJobRead:
    job = db.get(ImportJob, job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Import job not found")
    return ImportJobRead.model_validate(job)
