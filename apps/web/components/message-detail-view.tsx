'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';

import { MessageStatusBadge } from '@/components/message-status-badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { getMessage } from '@/lib/api';
import type { Message } from '@/lib/types';

export function MessageDetailView({ messageId }: { messageId: number }) {
  const [message, setMessage] = useState<Message | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    const loadMessage = async () => {
      try {
        const nextMessage = await getMessage(messageId);
        if (active) {
          setMessage(nextMessage);
        }
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Unable to load message');
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void loadMessage();

    return () => {
      active = false;
    };
  }, [messageId]);

  if (loading) {
    return <Card className="p-6 text-sm text-[var(--muted)]">Loading message details…</Card>;
  }

  if (!message) {
    return <Card className="p-6 text-sm text-[var(--muted)]">Message not found.</Card>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-[0.3em] text-[var(--muted)]">Message Detail</p>
          <h2 className="text-3xl font-semibold tracking-tight">Message #{message.id}</h2>
        </div>
        <Link href="/messages">
          <Button type="button" variant="outline">
            Back to messages
          </Button>
        </Link>
      </div>
      <Card className="space-y-4 p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-sm text-[var(--muted)]">{message.recipient_email}</p>
            <p className="text-lg font-semibold">{message.subject}</p>
          </div>
          <MessageStatusBadge status={message.status} />
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <Detail label="Provider ID" value={String(message.provider_id)} />
          <Detail label="Sender Identity ID" value={String(message.sender_identity_id)} />
          <Detail label="Attempt count" value={String(message.attempt_count)} />
          <Detail label="Created at" value={new Date(message.created_at).toLocaleString()} />
          <Detail label="Updated at" value={new Date(message.updated_at).toLocaleString()} />
          <Detail label="Sent at" value={message.sent_at ? new Date(message.sent_at).toLocaleString() : 'Not sent yet'} />
        </div>
        {message.error_message ? (
          <div className="rounded-2xl bg-rose-100 p-4 text-sm text-rose-700 dark:bg-rose-500/10 dark:text-rose-200">
            {message.error_message}
          </div>
        ) : null}
        <div className="space-y-2">
          <p className="text-sm font-medium">Plain text body</p>
          <pre className="whitespace-pre-wrap rounded-2xl border border-[var(--card-border)] bg-[var(--surface)] p-4 text-sm">{message.body_text}</pre>
        </div>
        {message.body_html ? (
          <div className="space-y-2">
            <p className="text-sm font-medium">HTML body</p>
            <pre className="whitespace-pre-wrap rounded-2xl border border-[var(--card-border)] bg-[var(--surface)] p-4 text-sm">{message.body_html}</pre>
          </div>
        ) : null}
      </Card>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--surface)] p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-[var(--muted)]">{label}</p>
      <p className="mt-2 text-sm">{value}</p>
    </div>
  );
}
