import type {
  Contact,
  ContactCreate,
  ContactList,
  ContactListCreate,
  ContactListMember,
  ContactUpdate,
  ImportJob,
  Message,
  MessageListResponse,
  MessageSendRequest,
  SenderIdentity,
  SenderIdentityCreate,
  SmtpProvider,
  SmtpProviderConnectionTest,
  SmtpProviderCreate,
  SuppressionCheckResponse,
  SuppressionEntry,
  Template,
  TemplateSummary,
  TemplatePreviewResponse,
  TemplateValidateResponse,
  TemplateVersion,
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

// ---------------------------------------------------------------------------
// Templates
// ---------------------------------------------------------------------------

export function listTemplates() {
  return request<TemplateSummary[]>('/templates');
}

export function getTemplate(templateId: number) {
  return request<Template>(`/templates/${templateId}`);
}

export function createTemplate(payload: {
  name: string;
  description?: string;
  subject_template: string;
  body_html_template?: string;
  body_text_template: string;
}) {
  return request<Template>('/templates', { method: 'POST', body: JSON.stringify(payload) });
}

export function updateTemplate(templateId: number, payload: { name: string; description?: string }) {
  return request<Template>(`/templates/${templateId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function createTemplateVersion(
  templateId: number,
  payload: {
    subject_template: string;
    body_html_template?: string;
    body_text_template: string;
    created_by?: string;
  },
) {
  return request<TemplateVersion>(`/templates/${templateId}/versions`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function listTemplateVersions(templateId: number) {
  return request<TemplateVersion[]>(`/templates/${templateId}/versions`);
}

export function rollbackTemplateVersion(templateId: number, versionId: number) {
  return request<Template>(`/templates/${templateId}/versions/${versionId}/rollback`, {
    method: 'POST',
  });
}

export function previewTemplate(
  templateId: number,
  payload: { variables: Record<string, string>; version_id?: number },
) {
  return request<TemplatePreviewResponse>(`/templates/${templateId}/preview`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function validateTemplate(
  templateId: number,
  payload: { variables: Record<string, string> },
) {
  return request<TemplateValidateResponse>(`/templates/${templateId}/validate`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

// ---------------------------------------------------------------------------
// Phase 4: Contacts
// ---------------------------------------------------------------------------

export function listContacts(status?: string) {
  const params = new URLSearchParams();
  if (status) params.set('status', status);
  const suffix = params.size ? `?${params.toString()}` : '';
  return request<Contact[]>(`/contacts${suffix}`);
}

export function getContact(contactId: number) {
  return request<Contact>(`/contacts/${contactId}`);
}

export function createContact(payload: ContactCreate) {
  return request<Contact>('/contacts', { method: 'POST', body: JSON.stringify(payload) });
}

export function updateContact(contactId: number, payload: ContactUpdate) {
  return request<Contact>(`/contacts/${contactId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function deleteContact(contactId: number) {
  return request<void>(`/contacts/${contactId}`, { method: 'DELETE' });
}

export function getContactLists_for_contact(contactId: number) {
  return request<ContactListMember[]>(`/contacts/${contactId}/lists`);
}

export function addContactToList(contactId: number, listId: number) {
  return request<ContactListMember>(`/contacts/${contactId}/lists/${listId}`, { method: 'POST' });
}

export function removeContactFromList(contactId: number, listId: number) {
  return request<void>(`/contacts/${contactId}/lists/${listId}`, { method: 'DELETE' });
}

// ---------------------------------------------------------------------------
// Phase 4: Contact Lists
// ---------------------------------------------------------------------------

export function listContactLists() {
  return request<ContactList[]>('/contact-lists');
}

export function createContactList(payload: ContactListCreate) {
  return request<ContactList>('/contact-lists', { method: 'POST', body: JSON.stringify(payload) });
}

export function updateContactList(listId: number, payload: ContactListCreate) {
  return request<ContactList>(`/contact-lists/${listId}`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}

export function deleteContactList(listId: number) {
  return request<void>(`/contact-lists/${listId}`, { method: 'DELETE' });
}

// ---------------------------------------------------------------------------
// Phase 4: Suppression
// ---------------------------------------------------------------------------

export function listSuppressions() {
  return request<SuppressionEntry[]>('/suppression');
}

export function checkSuppression(email: string) {
  return request<SuppressionCheckResponse>(`/suppression/check?email=${encodeURIComponent(email)}`);
}

export function addSuppression(payload: { email: string; reason: string; source?: string }) {
  return request<SuppressionEntry>('/suppression', { method: 'POST', body: JSON.stringify(payload) });
}

export function removeSuppression(suppressionId: number) {
  return request<void>(`/suppression/${suppressionId}`, { method: 'DELETE' });
}

// ---------------------------------------------------------------------------
// Phase 4: Import Jobs
// ---------------------------------------------------------------------------

export async function createImportJob(
  file: File,
  options?: { contactListId?: number; columnMapping?: Record<string, string> },
): Promise<ImportJob> {
  const form = new FormData();
  form.append('file', file);
  if (options?.contactListId != null) {
    form.append('contact_list_id', String(options.contactListId));
  }
  if (options?.columnMapping) {
    form.append('column_mapping', JSON.stringify(options.columnMapping));
  }

  const response = await fetch(`${API_BASE_URL}/import-jobs`, {
    method: 'POST',
    body: form,
    cache: 'no-store',
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
    throw new Error(payload?.detail ?? `Request failed with ${response.status}`);
  }
  return (await response.json()) as ImportJob;
}

export function getImportJob(jobId: number) {
  return request<ImportJob>(`/import-jobs/${jobId}`);
}

export function listImportJobs() {
  return request<ImportJob[]>('/import-jobs');
}
