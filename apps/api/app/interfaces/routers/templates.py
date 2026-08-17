from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.dependencies import get_db
from app.application.schemas import (
    PlaceholderInspectorResult,
    TemplateCreate,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
    TemplateRead,
    TemplateSummary,
    TemplateUpdate,
    TemplateValidateRequest,
    TemplateValidateResponse,
    TemplateVersionCreate,
    TemplateVersionRead,
)
from app.application.services.templates import inspect_placeholders, render_template
from app.domain.models import Template, TemplateVersion

router = APIRouter(prefix="/templates", tags=["templates"])


def _get_or_404(db: Session, template_id: int) -> Template:
    tmpl = db.get(Template, template_id)
    if tmpl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return tmpl


def _get_version_or_404(db: Session, version_id: int, template_id: int) -> TemplateVersion:
    ver = db.get(TemplateVersion, version_id)
    if ver is None or ver.template_id != template_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template version not found"
        )
    return ver


def _resolve_version(
    db: Session, tmpl: Template, version_id: int | None
) -> TemplateVersion:
    if version_id is not None:
        return _get_version_or_404(db, version_id, tmpl.id)
    if tmpl.current_version_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template has no current version",
        )
    ver = db.get(TemplateVersion, tmpl.current_version_id)
    if ver is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template current version not found",
        )
    return ver


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.post("", response_model=TemplateRead, status_code=status.HTTP_201_CREATED)
def create_template(payload: TemplateCreate, db: Session = Depends(get_db)) -> TemplateRead:
    tmpl = Template(name=payload.name, description=payload.description)
    db.add(tmpl)
    db.flush()  # get tmpl.id without committing

    ver = TemplateVersion(
        template_id=tmpl.id,
        version_number=1,
        subject_template=payload.subject_template,
        body_html_template=payload.body_html_template,
        body_text_template=payload.body_text_template,
        created_by=None,
    )
    db.add(ver)
    db.flush()

    tmpl.current_version_id = ver.id
    db.commit()
    db.refresh(tmpl)
    return TemplateRead.model_validate(tmpl)


@router.get("", response_model=list[TemplateSummary])
def list_templates(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[TemplateSummary]:
    rows = list(
        db.scalars(
            select(Template).order_by(Template.updated_at.desc()).limit(limit).offset(offset)
        )
    )
    return [TemplateSummary.model_validate(r) for r in rows]


@router.get("/{template_id}", response_model=TemplateRead)
def get_template(template_id: int, db: Session = Depends(get_db)) -> TemplateRead:
    return TemplateRead.model_validate(_get_or_404(db, template_id))


@router.put("/{template_id}", response_model=TemplateRead)
def update_template(
    template_id: int, payload: TemplateUpdate, db: Session = Depends(get_db)
) -> TemplateRead:
    tmpl = _get_or_404(db, template_id)
    tmpl.name = payload.name
    tmpl.description = payload.description
    db.commit()
    db.refresh(tmpl)
    return TemplateRead.model_validate(tmpl)


# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------

@router.post(
    "/{template_id}/versions",
    response_model=TemplateVersionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_version(
    template_id: int, payload: TemplateVersionCreate, db: Session = Depends(get_db)
) -> TemplateVersionRead:
    tmpl = _get_or_404(db, template_id)
    last_version_number = (
        db.scalar(
            select(TemplateVersion.version_number)
            .where(TemplateVersion.template_id == template_id)
            .order_by(TemplateVersion.version_number.desc())
            .limit(1)
        )
        or 0
    )
    ver = TemplateVersion(
        template_id=tmpl.id,
        version_number=last_version_number + 1,
        subject_template=payload.subject_template,
        body_html_template=payload.body_html_template,
        body_text_template=payload.body_text_template,
        created_by=payload.created_by,
    )
    db.add(ver)
    db.flush()
    tmpl.current_version_id = ver.id
    db.commit()
    db.refresh(ver)
    return TemplateVersionRead.model_validate(ver)


@router.get("/{template_id}/versions", response_model=list[TemplateVersionRead])
def list_versions(
    template_id: int, db: Session = Depends(get_db)
) -> list[TemplateVersionRead]:
    _get_or_404(db, template_id)
    rows = list(
        db.scalars(
            select(TemplateVersion)
            .where(TemplateVersion.template_id == template_id)
            .order_by(TemplateVersion.version_number)
        )
    )
    return [TemplateVersionRead.model_validate(r) for r in rows]


@router.post("/{template_id}/versions/{version_id}/rollback", response_model=TemplateRead)
def rollback_version(
    template_id: int, version_id: int, db: Session = Depends(get_db)
) -> TemplateRead:
    """Repoint ``current_version_id`` to an existing prior version.

    No new version row is created — the chosen version simply becomes current.
    """
    tmpl = _get_or_404(db, template_id)
    _get_version_or_404(db, version_id, template_id)
    tmpl.current_version_id = version_id
    db.commit()
    db.refresh(tmpl)
    return TemplateRead.model_validate(tmpl)


# ---------------------------------------------------------------------------
# Preview + validate
# ---------------------------------------------------------------------------

@router.post("/{template_id}/preview", response_model=TemplatePreviewResponse)
def preview_template(
    template_id: int, payload: TemplatePreviewRequest, db: Session = Depends(get_db)
) -> TemplatePreviewResponse:
    tmpl = _get_or_404(db, template_id)
    ver = _resolve_version(db, tmpl, payload.version_id)
    variables = payload.variables or {}
    result = render_template(
        ver.subject_template,
        ver.body_html_template,
        ver.body_text_template,
        variables,
    )
    return TemplatePreviewResponse(
        subject=result.subject,
        body_html=result.body_html,
        body_text=result.body_text,
        inspector=PlaceholderInspectorResult(
            used_placeholders=result.used_placeholders,
            missing_placeholders=result.missing_placeholders,
            unknown_payload_keys=result.unknown_payload_keys,
            all_present=len(result.missing_placeholders) == 0,
        ),
        html_safety_warnings=result.html_safety_warnings,
    )


@router.post("/{template_id}/validate", response_model=TemplateValidateResponse)
def validate_template(
    template_id: int, payload: TemplateValidateRequest, db: Session = Depends(get_db)
) -> TemplateValidateResponse:
    tmpl = _get_or_404(db, template_id)
    ver = _resolve_version(db, tmpl, None)
    variables = payload.variables or {}
    result = inspect_placeholders(
        ver.subject_template,
        ver.body_html_template,
        ver.body_text_template,
        variables,
    )
    return TemplateValidateResponse(
        valid=result.all_present,
        missing_placeholders=result.missing_placeholders,
    )
