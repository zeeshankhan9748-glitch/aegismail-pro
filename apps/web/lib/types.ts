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
  subject: string;
  body_text: string;
  body_html?: string;
  idempotency_key?: string;
};
