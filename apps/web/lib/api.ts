import type { SmtpProvider, SmtpProviderCreate } from '@/lib/types';

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
