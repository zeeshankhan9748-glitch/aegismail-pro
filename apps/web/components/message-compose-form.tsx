'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { LoaderCircle } from 'lucide-react';
import type { ReactNode } from 'react';
import { useEffect, useMemo } from 'react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { z } from 'zod';

import { sendMessage } from '@/lib/api';
import type { Message, SenderIdentity, SmtpProvider } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

const schema = z.object({
  provider_id: z.coerce.number().int().min(1, 'Provider is required'),
  sender_identity_id: z.coerce.number().int().min(1, 'Sender identity is required'),
  recipient_email: z.email('Enter a valid recipient email'),
  subject: z.string().min(1, 'Subject is required'),
  body_text: z.string().min(1, 'Plain text body is required'),
  body_html: z.string().optional(),
  idempotency_key: z.string().optional(),
});

type FormValues = z.input<typeof schema>;
type FormOutput = z.output<typeof schema>;

export function MessageComposeForm({
  providers,
  senderIdentities,
  onSent,
}: {
  providers: SmtpProvider[];
  senderIdentities: SenderIdentity[];
  onSent: (message: Message) => void;
}) {
  const {
    register,
    handleSubmit,
    watch,
    reset,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormValues, unknown, FormOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      provider_id: providers[0]?.id ?? 0,
      sender_identity_id: senderIdentities[0]?.id ?? 0,
      recipient_email: '',
      subject: '',
      body_text: '',
      body_html: '',
      idempotency_key: '',
    },
  });

  // React Hook Form exposes non-memoizable watch helpers here.
  // eslint-disable-next-line react-hooks/incompatible-library
  const providerId = watch('provider_id');
  const availableSenderIdentities = useMemo(
    () => senderIdentities.filter((identity) => identity.smtp_provider_id === providerId),
    [providerId, senderIdentities],
  );

  useEffect(() => {
    if (providers[0] && !providerId) {
      setValue('provider_id', providers[0].id);
    }
  }, [providerId, providers, setValue]);

  useEffect(() => {
    if (availableSenderIdentities.length) {
      setValue('sender_identity_id', availableSenderIdentities[0].id);
    }
  }, [availableSenderIdentities, setValue]);

  const onSubmit = handleSubmit(async (values: FormOutput) => {
    try {
      const message = await sendMessage({
        ...values,
        body_html: values.body_html || undefined,
        idempotency_key: values.idempotency_key || undefined,
      });
      toast.success(`Message ${message.status}`);
      onSent(message);
      reset({
        provider_id: values.provider_id,
        sender_identity_id: availableSenderIdentities[0]?.id ?? 0,
        recipient_email: '',
        subject: '',
        body_text: '',
        body_html: '',
        idempotency_key: '',
      });
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Unable to queue message');
    }
  });

  return (
    <Card className="p-6">
      <div className="mb-5 space-y-1">
        <h3 className="text-lg font-semibold">Send Test Email</h3>
        <p className="text-sm text-[var(--muted)]">Queue a single one-off message through Celery and watch it move through the delivery lifecycle.</p>
      </div>
      <form className="space-y-4" onSubmit={onSubmit}>
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="SMTP Provider" error={errors.provider_id?.message?.toString()}>
            <select
              {...register('provider_id')}
              className="w-full rounded-2xl border border-[var(--card-border)] bg-[var(--surface)] px-4 py-3 text-sm outline-none"
              disabled={!providers.length}
            >
              {providers.length ? (
                providers.map((provider) => (
                  <option key={provider.id} value={provider.id}>
                    {provider.name}
                  </option>
                ))
              ) : (
                <option value="">Create an SMTP provider first</option>
              )}
            </select>
          </Field>
          <Field label="Sender Identity" error={errors.sender_identity_id?.message?.toString()}>
            <select
              {...register('sender_identity_id')}
              className="w-full rounded-2xl border border-[var(--card-border)] bg-[var(--surface)] px-4 py-3 text-sm outline-none"
              disabled={!availableSenderIdentities.length}
            >
              {availableSenderIdentities.length ? (
                availableSenderIdentities.map((identity) => (
                  <option key={identity.id} value={identity.id}>
                    {identity.display_name} · {identity.from_email}
                  </option>
                ))
              ) : (
                <option value="">Create a sender identity for this provider first</option>
              )}
            </select>
          </Field>
          <Field label="Recipient" error={errors.recipient_email?.message}>
            <Input {...register('recipient_email')} placeholder="recipient@example.com" />
          </Field>
          <Field label="Subject" error={errors.subject?.message}>
            <Input {...register('subject')} placeholder="Your test email" />
          </Field>
        </div>
        <Field label="Plain text body" error={errors.body_text?.message}>
          <textarea
            {...register('body_text')}
            rows={5}
            className="w-full rounded-2xl border border-[var(--card-border)] bg-[var(--surface)] px-4 py-3 text-sm outline-none"
            placeholder="Hello from AegisMail Pro"
          />
        </Field>
        <Field label="HTML body (optional)" error={errors.body_html?.message}>
          <textarea
            {...register('body_html')}
            rows={5}
            className="w-full rounded-2xl border border-[var(--card-border)] bg-[var(--surface)] px-4 py-3 text-sm outline-none"
            placeholder="<p>Hello from <strong>AegisMail Pro</strong></p>"
          />
        </Field>
        <Field label="Idempotency key (optional)" error={errors.idempotency_key?.message}>
          <Input {...register('idempotency_key')} placeholder="send-test-123" />
        </Field>
        <Button type="submit" disabled={isSubmitting || !providers.length || !availableSenderIdentities.length}>
          {isSubmitting ? <LoaderCircle className="size-4 animate-spin" /> : null}
          {isSubmitting ? 'Queueing…' : 'Send test email'}
        </Button>
      </form>
    </Card>
  );
}

function Field({ label, error, children }: { label: string; error?: string; children: ReactNode }) {
  return (
    <label className="space-y-2 text-sm">
      <span className="font-medium">{label}</span>
      {children}
      {error ? <span className="text-xs text-rose-600 dark:text-rose-300">{error}</span> : null}
    </label>
  );
}
