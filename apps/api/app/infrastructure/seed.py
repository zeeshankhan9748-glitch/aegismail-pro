from sqlalchemy import select

from app.application.security import encrypt_secret, hash_api_key, hash_password
from app.domain.models import APIKey, Role, SenderIdentity, SMTPProvider, User
from app.infrastructure.database import Base, SessionLocal, engine
from app.settings import get_settings

ROLE_NAMES = ["admin", "operator", "viewer"]


def seed() -> None:
    settings = get_settings()
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        roles: dict[str, Role] = {}
        for role_name in ROLE_NAMES:
            role = session.scalar(select(Role).where(Role.name == role_name))
            if role is None:
                role = Role(name=role_name, description=f"{role_name.title()} role")
                session.add(role)
                session.flush()
            roles[role_name] = role

        admin = session.scalar(select(User).where(User.username == settings.default_admin_username))
        if admin is None:
            admin = User(
                username=settings.default_admin_username,
                email=settings.default_admin_email,
                password_hash=hash_password(settings.default_admin_password),
                role=roles["admin"],
            )
            session.add(admin)
            session.flush()

        api_key_value = "amp_demo_key_12345"
        api_key = session.scalar(select(APIKey).where(APIKey.name == "Demo CLI Key"))
        if api_key is None:
            session.add(
                APIKey(
                    user=admin,
                    name="Demo CLI Key",
                    key_prefix=api_key_value[:8],
                    key_hash=hash_api_key(api_key_value),
                )
            )

        provider = session.scalar(select(SMTPProvider).where(SMTPProvider.name == "Demo SMTP"))
        if provider is None:
            provider = SMTPProvider(
                name="Demo SMTP",
                host="smtp.demo.local",
                port=587,
                username="demo-user",
                password_encrypted=encrypt_secret(settings.demo_smtp_password),
                use_tls=True,
            )
            session.add(provider)
            session.flush()

        identity = session.scalar(
            select(SenderIdentity).where(SenderIdentity.from_email == "noreply@demo.local")
        )
        if identity is None:
            session.add(
                SenderIdentity(
                    smtp_provider=provider,
                    display_name="Demo Notifications",
                    from_email="noreply@demo.local",
                    reply_to_email="support@demo.local",
                )
            )

        session.commit()
        print("Seed complete.")
        print(f"Username: {settings.default_admin_username}")
        print("Seeded demo password comes from DEFAULT_ADMIN_PASSWORD in your local .env file.")
        print("API key and bearer token output are intentionally suppressed.")
    finally:
        session.close()


if __name__ == "__main__":
    seed()
