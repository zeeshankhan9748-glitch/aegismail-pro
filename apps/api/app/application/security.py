import hashlib
from datetime import UTC, datetime, timedelta

import jwt
from cryptography.fernet import Fernet
from pwdlib import PasswordHash

from app.settings import get_settings

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_hasher.verify(password, password_hash)


def create_access_token(subject: str, role: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, str]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def encrypt_secret(secret: str) -> str:
    key = get_settings().app_encryption_key.encode()
    return Fernet(key).encrypt(secret.encode()).decode()


def decrypt_secret(secret: str) -> str:
    key = get_settings().app_encryption_key.encode()
    return Fernet(key).decrypt(secret.encode()).decode()


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()
