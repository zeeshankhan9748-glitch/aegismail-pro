'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { LoaderCircle } from 'lucide-react';
import type { ReactNode } from 'react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { z } from 'zod';

import { createSmtpProvider, updateSmtpProvider } from '@/lib/api';
import type { SmtpProvider } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

const schema = z
  .object({
    name: z.string().min(1, 'Name is required'),
    host: z.string().min(1, 'Host is required'),
    port: z.coerce.number().int().min(1).max(65535),
    username: z.string().optional(),
    password: z.string().optional(),
    security: z.enum(['starttls', 'ssl', 'none']),
    throttle_limit_per_minute: z.coerce.number().int().min(1).max(10000),
  })
  .transform((values) => ({
    name: values.name,
    host: values.host,
    port: values.port,
    username: values.username || undefined,
    password: values.password || undefined,
    use_tls: values.security === 'starttls',
    use_ssl: values.security === 'ssl',
    throttle_limit_per_minute: values.throttle_limit_per_minute,
  }));

type FormValues = z.input<typeof schema>;
type FormOutput = z.output<typeof schema>;

const defaults: FormValues = {
  name: '',
  host: '',
  port: 587,
  username: '',
  password: '',
  security: 'starttls',
  throttle_limit_per_minute: 60,
};

function providerToDefaults(provider: SmtpProvider): FormValues {
  return {
    name: provider.name,
    host: provider.host,
    port: provider.port,
    username: provider.username ?? '',
    password: '',
    security: provider.use_ssl ? 'ssl' : provider.use_tls ? 'starttls' : 'none',
    throttle_limit_per_minute: provider.throttle_limit_per_minute,
  };
}

export function SmtpProviderForm({
  editingProvider,
  onCreated,
  onUpdated,
  onCancelEdit,
}: {
  editingProvider?: SmtpProvider | null;
  onCreated: (provider: SmtpProvider) => void;
  onUpdated: (provider: SmtpProvider) => void;
  onCancelEdit: () => void;
}) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues, unknown, FormOutput>({
    resolver: zodResolver(schema),
    defaultValues: defaults,
  });

  useEffect(() => {
    reset(editingProvider ? providerToDefaults(editingProvider) : defaults);
  }, [editingProvider, reset]);

  const onSubmit = handleSubmit(async (values: FormOutput) => {
    try {
      const provider = editingProvider
        ? await updateSmtpProvider(editingProvider.id, values)
        : await createSmtpProvider(values);
      toast.success(editingProvider ? 'SMTP provider updated' : 'SMTP provider created');
      if (editingProvider) {
        onUpdated(provider);
      } else {
        onCreated(provider);
      }
      reset(defaults);
      onCancelEdit();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to save SMTP provider';
      toast.error(message);
    }
  });

  return (
    <Card className="p-6">
      <div className="mb-5 space-y-1">
        <h3 className="text-lg font-semibold">{editingProvider ? 'Edit SMTP Provider' : 'Create SMTP Provider'}</h3>
        <p className="text-sm text-[var(--muted)]">Store SMTP credentials encrypted at rest, choose the connection mode, and set a simple provider throttle.</p>
      </div>
      <form className="space-y-4" onSubmit={onSubmit}>
        <div className="grid gap-4 md:grid-cols-2">
          <Field label="Name" error={errors.name?.message}>
            <Input {...register('name')} placeholder="Primary SMTP" />
          </Field>
          <Field label="Host" error={errors.host?.message}>
            <Input {...register('host')} placeholder="smtp.example.com" />
          </Field>
          <Field label="Port" error={errors.port?.message?.toString()}>
            <Input type="number" {...register('port')} />
          </Field>
          <Field label="Username" error={errors.username?.message}>
            <Input {...register('username')} placeholder="mailer" />
          </Field>
          <Field label={editingProvider ? 'Password (leave blank to keep current)' : 'Password'} error={errors.password?.message}>
            <Input type="password" {...register('password')} placeholder="Encrypted on the API side" />
          </Field>
          <Field label="Connection security">
            <select
              {...register('security')}
              className="w-full rounded-2xl border border-[var(--card-border)] bg-[var(--surface)] px-4 py-3 text-sm outline-none"
            >
              <option value="starttls">STARTTLS</option>
              <option value="ssl">SSL/TLS</option>
              <option value="none">None</option>
            </select>
          </Field>
          <Field label="Throttle limit / minute" error={errors.throttle_limit_per_minute?.message?.toString()}>
            <Input type="number" {...register('throttle_limit_per_minute')} />
          </Field>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? <LoaderCircle className="size-4 animate-spin" /> : null}
            {isSubmitting ? 'Saving…' : editingProvider ? 'Save changes' : 'Create provider'}
          </Button>
          {editingProvider ? (
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                reset(defaults);
                onCancelEdit();
              }}
            >
              Cancel edit
            </Button>
          ) : null}
        </div>
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
