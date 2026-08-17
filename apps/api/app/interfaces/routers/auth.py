from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.dependencies import get_api_key_record, get_current_user, get_db, require_role
from app.application.schemas import TokenResponse, UserResponse
from app.application.security import create_access_token, verify_password
from app.domain.models import APIKey, User
from app.rate_limit import limiter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse, summary="Login with local credentials")
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = db.scalar(
        select(User).where(User.username == form_data.username, User.is_active.is_(True))
    )
    if user is None or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=user.username, role=user.role.name)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse, summary="Inspect authenticated user")
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.name,
    )


@router.get("/admin-check", response_model=UserResponse, summary="RBAC proof endpoint")
def admin_check(current_user: User = Depends(require_role(["admin", "operator"]))) -> UserResponse:
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role.name,
    )


@router.get("/api-key-check", summary="API key auth proof endpoint")
def api_key_check(api_key: APIKey = Depends(get_api_key_record)) -> dict[str, str]:
    return {"status": "ok", "key_name": api_key.name, "owner": api_key.user.username}
