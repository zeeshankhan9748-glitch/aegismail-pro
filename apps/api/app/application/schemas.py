from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


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
    use_ssl: bool = False
    throttle_limit_per_minute: int = Field(default=60, ge=1, le=10_000)

    @model_validator(mode="after")
    def validate_security_mode(self) -> "SMTPProviderCreate":
        if self.use_tls and self.use_ssl:
            raise ValueError("TLS and SSL cannot both be enabled at the same time")
        return self


class SMTPProviderUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(ge=1, le=65535)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=255)
    use_tls: bool = True
    use_ssl: bool = False
    throttle_limit_per_minute: int = Field(default=60, ge=1, le=10_000)

    @model_validator(mode="after")
    def validate_security_mode(self) -> "SMTPProviderUpdate":
        if self.use_tls and self.use_ssl:
            raise ValueError("TLS and SSL cannot both be enabled at the same time")
        return self


class SMTPProviderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    host: str
    port: int
    username: str | None
    use_tls: bool
    use_ssl: bool
    throttle_limit_per_minute: int
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


class SMTPConnectionTestResponse(BaseModel):
    success: bool
    provider_id: int
    message: str


class MessageSendRequest(BaseModel):
    provider_id: int
    sender_identity_id: int
    recipient_email: EmailStr
    subject: str = Field(min_length=1, max_length=255)
    body_text: str = Field(min_length=1)
    body_html: str | None = None
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=255)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_id: int
    sender_identity_id: int
    recipient_email: EmailStr
    subject: str
    body_text: str
    body_html: str | None
    status: str
    error_message: str | None
    idempotency_key: str | None
    attempt_count: int
    created_at: datetime
    updated_at: datetime
    sent_at: datetime | None


class MessageSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider_id: int
    sender_identity_id: int
    provider_name: str
    sender_display_name: str
    recipient_email: EmailStr
    subject: str
    status: str
    error_message: str | None
    attempt_count: int
    created_at: datetime
    updated_at: datetime
    sent_at: datetime | None


class MessageListResponse(BaseModel):
    items: list[MessageSummary]
    total: int
    limit: int
    offset: int


class HealthResponse(BaseModel):
    status: str
    detail: str
