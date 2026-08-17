'use client';

import { RefreshCw } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';

import { MessageComposeForm } from '@/components/message-compose-form';
import { MessagesSkeleton } from '@/components/messages-skeleton';
import { MessagesTable } from '@/components/messages-table';
import { MessageStatusBadge } from '@/components/message-status-badge';
import { SenderIdentityForm } from '@/components/sender-identity-form';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { listMessages, listSenderIdentities, listSmtpProviders } from '@/lib/api';
import type { Message, MessageSummary, SenderIdentity, SmtpProvider } from '@/lib/types';

const ACTIVE_STATUSES: Message['status'][] = ['queued', 'processing', 'deferred'];

export function MessagesView() {
  const [providers, setProviders] = useState<SmtpProvider[]>([]);
  const [senderIdentities, setSenderIdentities] = useState<SenderIdentity[]>([]);
  const [messages, setMessages] = useState<MessageSummary[]>([]);
  const [statusFilter, setStatusFilter] = useState<'all' | Message['status']>('all');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const refreshData = useCallback(
    async (selectedStatus: 'all' | Message['status'] = statusFilter) => {
      try {
        setRefreshing(true);
        const [providersResponse, senderIdentitiesResponse, messagesResponse] = await Promise.all([
          listSmtpProviders(),
          listSenderIdentities(),
          listMessages(selectedStatus),
        ]);
        setProviders(providersResponse);
        setSenderIdentities(senderIdentitiesResponse);
        setMessages(messagesResponse.items);
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Unable to fetch message workspace data');
      } finally {
        setRefreshing(false);
        setLoading(false);
      }
    },
    [statusFilter],
  );

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refreshData();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [refreshData]);

  const hasActiveMessages = useMemo(
    () => messages.some((message) => ACTIVE_STATUSES.includes(message.status)),
    [messages],
  );

  useEffect(() => {
    if (!hasActiveMessages) {
      return;
    }
    const timer = window.setInterval(() => {
      void refreshData();
    }, 5000);
    return () => window.clearInterval(timer);
  }, [hasActiveMessages, refreshData]);

  const latestMessage = messages[0];

  return (
    <div className="grid gap-6 xl:grid-cols-[380px_minmax(0,1fr)]">
      <div className="space-y-6">
        <SenderIdentityForm
          providers={providers}
          onCreated={(identity) => setSenderIdentities((current) => [identity, ...current])}
        />
        <MessageComposeForm
          providers={providers}
          senderIdentities={senderIdentities}
          onSent={() => {
            void refreshData();
          }}
        />
      </div>
      <div className="space-y-4">
        <Card className="space-y-4 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <Badge variant="success">Celery-backed delivery</Badge>
              <h3 className="mt-3 text-lg font-semibold">Message lifecycle</h3>
              <p className="mt-1 text-sm text-[var(--muted)]">Queued sends update to processing, sent, deferred, or failed based on the worker outcome.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <select
                value={statusFilter}
                onChange={(event) => {
                  const nextValue = event.target.value as 'all' | Message['status'];
                  setStatusFilter(nextValue);
                  void refreshData(nextValue);
                }}
                className="rounded-2xl border border-[var(--card-border)] bg-[var(--surface)] px-4 py-3 text-sm outline-none"
              >
                <option value="all">All statuses</option>
                <option value="queued">Queued</option>
                <option value="processing">Processing</option>
                <option value="sent">Sent</option>
                <option value="deferred">Deferred</option>
                <option value="failed">Failed</option>
              </select>
              <Button type="button" variant="outline" disabled={refreshing} onClick={() => void refreshData()}>
                <RefreshCw className={refreshing ? 'size-4 animate-spin' : 'size-4'} />
                Refresh
              </Button>
            </div>
          </div>
          {latestMessage ? (
            <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--surface)] p-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-medium">Latest message</p>
                  <p className="text-sm text-[var(--muted)]">
                    {latestMessage.recipient_email} · {latestMessage.subject}
                  </p>
                </div>
                <MessageStatusBadge status={latestMessage.status} />
              </div>
              {latestMessage.error_message ? (
                <p className="mt-3 text-sm text-rose-600 dark:text-rose-300">{latestMessage.error_message}</p>
              ) : null}
            </div>
          ) : (
            <p className="text-sm text-[var(--muted)]">No messages yet. Create a sender identity and send your first test email.</p>
          )}
        </Card>
        {loading ? <MessagesSkeleton /> : <MessagesTable data={messages} />}
      </div>
    </div>
  );
}
