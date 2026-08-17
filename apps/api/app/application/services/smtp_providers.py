from sqlalchemy import select
from sqlalchemy.orm import Session

from app.application.schemas import SMTPProviderCreate, SMTPProviderUpdate
from app.application.security import encrypt_secret
from app.domain.models import SMTPProvider


def list_smtp_providers(db: Session) -> list[SMTPProvider]:
    return list(db.scalars(select(SMTPProvider).order_by(SMTPProvider.name.asc())))


def get_smtp_provider(db: Session, provider_id: int) -> SMTPProvider | None:
    return db.get(SMTPProvider, provider_id)


def create_smtp_provider(db: Session, payload: SMTPProviderCreate) -> SMTPProvider:
    provider = SMTPProvider(
        name=payload.name,
        host=payload.host,
        port=payload.port,
        username=payload.username,
        password_encrypted=encrypt_secret(payload.password) if payload.password else None,
        use_tls=payload.use_tls,
        use_ssl=payload.use_ssl,
        throttle_limit_per_minute=payload.throttle_limit_per_minute,
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


def update_smtp_provider(
    db: Session, provider: SMTPProvider, payload: SMTPProviderUpdate
) -> SMTPProvider:
    provider.name = payload.name
    provider.host = payload.host
    provider.port = payload.port
    provider.username = payload.username
    provider.use_tls = payload.use_tls
    provider.use_ssl = payload.use_ssl
    provider.throttle_limit_per_minute = payload.throttle_limit_per_minute
    if payload.password is not None:
        provider.password_encrypted = encrypt_secret(payload.password) if payload.password else None
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider
