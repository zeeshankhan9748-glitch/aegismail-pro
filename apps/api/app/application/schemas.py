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


class SMTPProviderBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(ge=1, le=65535)
    username: str | None = Field(default=None, max_length=255)
    use_tls: bool = True
    use_ssl: bool = False
    throttle_limit_per_minute: int = Field(default=60, ge=1, le=10_000)

    @model_validator(mode="after")
    def validate_security_mode(self) -> "SMTPProviderBase":
        if self.use_tls and self.use_ssl:
            raise ValueError("TLS and SSL cannot both be enabled at the same time")
        return self


class SMTPProviderCreate(SMTPProviderBase):
    password: str | None = Field(default=None, min_length=1, max_length=255)


class SMTPProviderUpdate(SMTPProviderBase):
    password: str | None = Field(default=None, max_length=255)


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
    subject: str | None = Field(default=None, min_length=1, max_length=255)
    body_text: str | None = Field(default=None, min_length=1)
    body_html: str | None = None
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=255)
    # Template-based sending (alternative to raw subject/body)
    template_id: int | None = None
    template_version_id: int | None = None
    variables: dict[str, str] | None = None

    @model_validator(mode="after")
    def validate_content_source(self) -> "MessageSendRequest":
        has_raw = bool(self.subject and self.body_text)
        has_template = self.template_id is not None
        if not has_raw and not has_template:
            raise ValueError(
                "Provide either (subject + body_text) or (template_id) as the message content source"
            )
        return self


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


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

class TemplateVersionCreate(BaseModel):
    subject_template: str = Field(min_length=1, max_length=255)
    body_html_template: str | None = None
    body_text_template: str = Field(min_length=1)
    created_by: str | None = None


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    subject_template: str = Field(min_length=1, max_length=255)
    body_html_template: str | None = None
    body_text_template: str = Field(min_length=1)


class TemplateUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class TemplateVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_id: int
    version_number: int
    subject_template: str
    body_html_template: str | None
    body_text_template: str
    created_at: datetime
    created_by: str | None


class TemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    current_version_id: int | None
    created_at: datetime
    updated_at: datetime
    current_version: TemplateVersionRead | None = None


class TemplateSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    current_version_id: int | None
    updated_at: datetime


class PlaceholderInspectorResult(BaseModel):
    used_placeholders: list[str]
    missing_placeholders: list[str]
    unknown_payload_keys: list[str]
    all_present: bool


class TemplatePreviewRequest(BaseModel):
    variables: dict[str, str] = Field(default_factory=dict)
    version_id: int | None = None


class TemplatePreviewResponse(BaseModel):
    subject: str
    body_html: str | None
    body_text: str
    inspector: PlaceholderInspectorResult
    html_safety_warnings: list[str]


class TemplateValidateRequest(BaseModel):
    variables: dict[str, str] = Field(default_factory=dict)


class TemplateValidateResponse(BaseModel):
    valid: bool
    missing_placeholders: list[str]


# ---------------------------------------------------------------------------
# Phase 4: Contacts, Contact Lists, Suppression, Import Jobs
# ---------------------------------------------------------------------------

VALID_CONTACT_STATUSES = {"active", "unsubscribed", "bounced", "complained"}
VALID_SUPPRESSION_REASONS = {"unsubscribed", "bounced", "complained", "manual"}


class ContactCreate(BaseModel):
    email: EmailStr
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    custom_fields: dict | None = None
    status: str = Field(default="active")

    @model_validator(mode="after")
    def validate_status(self) -> "ContactCreate":
        if self.status not in VALID_CONTACT_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(sorted(VALID_CONTACT_STATUSES))}")
        return self


class ContactUpdate(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    custom_fields: dict | None = None
    status: str | None = None

    @model_validator(mode="after")
    def validate_status(self) -> "ContactUpdate":
        if self.status is not None and self.status not in VALID_CONTACT_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(sorted(VALID_CONTACT_STATUSES))}")
        return self


class ContactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    first_name: str | None
    last_name: str | None
    custom_fields: dict | None
    status: str
    created_at: datetime
    updated_at: datetime
    list_count: int = 0


class ContactListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class ContactListUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class ContactListRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
    member_count: int = 0


class ContactListMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contact_list_id: int
    contact_id: int
    added_at: datetime


class SuppressionEntryCreate(BaseModel):
    email: EmailStr
    reason: str = Field(default="manual")
    source: str = Field(default="manual", max_length=64)

    @model_validator(mode="after")
    def validate_reason(self) -> "SuppressionEntryCreate":
        if self.reason not in VALID_SUPPRESSION_REASONS:
            raise ValueError(
                f"reason must be one of: {', '.join(sorted(VALID_SUPPRESSION_REASONS))}"
            )
        return self


class SuppressionEntryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    reason: str
    source: str
    created_at: datetime


class SuppressionCheckResponse(BaseModel):
    email: str
    suppressed: bool
    reason: str | None
    source: str | None


class ImportJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    status: str
    total_rows: int
    processed_rows: int
    imported_count: int
    skipped_count: int
    error_count: int
    error_report: list | None
    contact_list_id: int | None
    created_at: datetime
    completed_at: datetime | None
