from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    role: str


class SMTPProviderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(ge=1, le=65535)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=1, max_length=255)
    use_tls: bool = True


class SMTPProviderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    host: str
    port: int
    username: str | None
    use_tls: bool
    created_at: datetime


class SenderIdentityCreate(BaseModel):
    smtp_provider_id: int
    display_name: str = Field(min_length=1, max_length=120)
    from_email: EmailStr
    reply_to_email: EmailStr | None = None


class SenderIdentityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    smtp_provider_id: int
    display_name: str
    from_email: EmailStr
    reply_to_email: EmailStr | None
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    detail: str
