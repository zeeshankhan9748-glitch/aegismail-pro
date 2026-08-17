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

// ---------------------------------------------------------------------------
// Phase 4: Contacts, Contact Lists, Suppression, Import Jobs
// ---------------------------------------------------------------------------

export type ContactStatus = 'active' | 'unsubscribed' | 'bounced' | 'complained';

export type Contact = {
  id: number;
  email: string;
  first_name: string | null;
  last_name: string | null;
  custom_fields: Record<string, unknown> | null;
  status: ContactStatus;
  created_at: string;
  updated_at: string;
  list_count: number;
};

export type ContactCreate = {
  email: string;
  first_name?: string;
  last_name?: string;
  custom_fields?: Record<string, unknown>;
  status?: ContactStatus;
};

export type ContactUpdate = Partial<ContactCreate>;

export type ContactList = {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  member_count: number;
};

export type ContactListCreate = {
  name: string;
  description?: string;
};

export type ContactListMember = {
  id: number;
  contact_list_id: number;
  contact_id: number;
  added_at: string;
};

export type SuppressionEntry = {
  id: number;
  email: string;
  reason: string;
  source: string;
  created_at: string;
};

export type SuppressionCheckResponse = {
  email: string;
  suppressed: boolean;
  reason: string | null;
  source: string | null;
};

export type ImportJob = {
  id: number;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  total_rows: number;
  processed_rows: number;
  imported_count: number;
  skipped_count: number;
  error_count: number;
  error_report: Array<{ row: number; error: string }> | null;
  contact_list_id: number | null;
  created_at: string;
  completed_at: string | null;
};
