'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { LoaderCircle } from 'lucide-react';
import type { ReactNode } from 'react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { z } from 'zod';

import { createSenderIdentity } from '@/lib/api';
import type { SenderIdentity, SmtpProvider } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

const schema = z.object({
  smtp_provider_id: z.coerce.number().int().min(1, 'Provider is required'),
  display_name: z.string().min(1, 'Display name is required'),
  from_email: z.email('Enter a valid from email'),
  reply_to_email: z.string().optional().refine((value) => !value || z.email().safeParse(value).success, {
    message: 'Enter a valid reply-to email',
  }),
});

type FormValues = z.input<typeof schema>;
type FormOutput = z.output<typeof schema>;

export function SenderIdentityForm({
  providers,
  onCreated,
}: {
  providers: SmtpProvider[];
  onCreated: (identity: SenderIdentity) => void;
}) {
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormValues, unknown, FormOutput>({
    resolver: zodResolver(schema),
    defaultValues: {
      smtp_provider_id: providers[0]?.id ?? 0,
      display_name: '',
      from_email: '',
      reply_to_email: '',
    },
  });

  useEffect(() => {
    if (providers[0]) {
      setValue('smtp_provider_id', providers[0].id);
    }
  }, [providers, setValue]);

  const onSubmit = handleSubmit(async (values) => {
    try {
      const identity = await createSenderIdentity(values);
      toast.success('Sender identity created');
      onCreated(identity);
      reset({
        smtp_provider_id: providers[0]?.id ?? values.smtp_provider_id,
        display_name: '',
        from_email: '',
        reply_to_email: '',
      });
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Unable to create sender identity');
    }
  });

  return (
    <Card className="p-6">
      <div className="mb-5 space-y-1">
        <h3 className="text-lg font-semibold">Create Sender Identity</h3>
        <p className="text-sm text-[var(--muted)]">Choose the provider this sender belongs to, then use it for one-off test sends.</p>
      </div>
      <form className="space-y-4" onSubmit={onSubmit}>
        <Field label="SMTP Provider" error={errors.smtp_provider_id?.message?.toString()}>
          <select
            {...register('smtp_provider_id')}
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
        <Field label="Display name" error={errors.display_name?.message}>
          <Input {...register('display_name')} placeholder="Demo Notifications" />
        </Field>
        <Field label="From email" error={errors.from_email?.message}>
          <Input {...register('from_email')} placeholder="noreply@example.com" />
        </Field>
        <Field label="Reply-to email" error={errors.reply_to_email?.message}>
          <Input {...register('reply_to_email')} placeholder="support@example.com" />
        </Field>
        <Button type="submit" disabled={isSubmitting || !providers.length}>
          {isSubmitting ? <LoaderCircle className="size-4 animate-spin" /> : null}
          {isSubmitting ? 'Saving…' : 'Create sender identity'}
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
