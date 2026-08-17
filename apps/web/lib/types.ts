export type SmtpProvider = {
  id: number;
  name: string;
  host: string;
  port: number;
  username: string | null;
  use_tls: boolean;
  use_ssl: boolean;
  throttle_limit_per_minute: number;
  created_at: string;
};

export type SmtpProviderCreate = {
  name: string;
  host: string;
  port: number;
  username?: string;
  password?: string;
  use_tls: boolean;
  use_ssl: boolean;
  throttle_limit_per_minute: number;
};

export type SmtpProviderConnectionTest = {
  success: boolean;
  provider_id: number;
  message: string;
};

export type SenderIdentity = {
  id: number;
  smtp_provider_id: number;
  display_name: string;
  from_email: string;
  reply_to_email: string | null;
  created_at: string;
};

export type SenderIdentityCreate = {
  smtp_provider_id: number;
  display_name: string;
  from_email: string;
  reply_to_email?: string;
};

export type Message = {
  id: number;
  provider_id: number;
  sender_identity_id: number;
  recipient_email: string;
  subject: string;
  body_text: string;
  body_html: string | null;
  status: 'queued' | 'processing' | 'sent' | 'failed' | 'deferred';
  error_message: string | null;
  idempotency_key: string | null;
  attempt_count: number;
  created_at: string;
  updated_at: string;
  sent_at: string | null;
};

export type MessageSummary = {
  id: number;
  provider_id: number;
  sender_identity_id: number;
  provider_name: string;
  sender_display_name: string;
  recipient_email: string;
  subject: string;
  status: Message['status'];
  error_message: string | null;
  attempt_count: number;
  created_at: string;
  updated_at: string;
  sent_at: string | null;
};

export type MessageListResponse = {
  items: MessageSummary[];
  total: number;
  limit: number;
  offset: number;
};

export type MessageSendRequest = {
  provider_id: number;
  sender_identity_id: number;
  recipient_email: string;
  subject?: string;
  body_text?: string;
  body_html?: string;
  idempotency_key?: string;
  template_id?: number;
  template_version_id?: number;
  variables?: Record<string, string>;
};

// ---------------------------------------------------------------------------
// Templates
// ---------------------------------------------------------------------------

export type TemplateVersion = {
  id: number;
  template_id: number;
  version_number: number;
  subject_template: string;
  body_html_template: string | null;
  body_text_template: string;
  created_at: string;
  created_by: string | null;
};

export type Template = {
  id: number;
  name: string;
  description: string | null;
  current_version_id: number | null;
  created_at: string;
  updated_at: string;
  current_version: TemplateVersion | null;
};

export type TemplateSummary = {
  id: number;
  name: string;
  description: string | null;
  current_version_id: number | null;
  updated_at: string;
};

export type PlaceholderInspectorResult = {
  used_placeholders: string[];
  missing_placeholders: string[];
  unknown_payload_keys: string[];
  all_present: boolean;
};

export type TemplatePreviewResponse = {
  subject: string;
  body_html: string | null;
  body_text: string;
  inspector: PlaceholderInspectorResult;
  html_safety_warnings: string[];
};

export type TemplateValidateResponse = {
  valid: boolean;
  missing_placeholders: string[];
};
