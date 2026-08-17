import type {
  Message,
  MessageListResponse,
  MessageSendRequest,
  SenderIdentity,
  SenderIdentityCreate,
  SmtpProvider,
  SmtpProviderConnectionTest,
  SmtpProviderCreate,
} from '@/lib/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    cache: 'no-store',
  });

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with ${response.status}`);
  }

  return (await response.json()) as T;
}

export function listSmtpProviders() {
  return request<SmtpProvider[]>('/smtp-providers');
}

export function createSmtpProvider(payload: SmtpProviderCreate) {
  return request<SmtpProvider>('/smtp-providers', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function updateSmtpProvider(providerId: number, payload: SmtpProviderCreate) {
  return request<SmtpProvider>(`/smtp-providers/${providerId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function testSmtpProviderConnection(providerId: number) {
  return request<SmtpProviderConnectionTest>(`/smtp-providers/${providerId}/test-connection`, {
    method: 'POST',
  });
}

export function listSenderIdentities() {
  return request<SenderIdentity[]>('/sender-identities');
}

export function createSenderIdentity(payload: SenderIdentityCreate) {
  return request<SenderIdentity>('/sender-identities', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function sendMessage(payload: MessageSendRequest) {
  return request<Message>('/messages/send', {
    method: 'POST',
    headers: payload.idempotency_key ? { 'Idempotency-Key': payload.idempotency_key } : undefined,
    body: JSON.stringify(payload),
  });
}

export function listMessages(status?: string) {
  const params = new URLSearchParams();
  if (status && status !== 'all') {
    params.set('status', status);
  }
  const suffix = params.size ? `?${params.toString()}` : '';
  return request<MessageListResponse>(`/messages${suffix}`);
}

export function getMessage(messageId: number) {
  return request<Message>(`/messages/${messageId}`);
}
