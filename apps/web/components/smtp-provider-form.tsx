'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { LoaderCircle } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { z } from 'zod';

import { createSmtpProvider } from '@/lib/api';
import type { SmtpProvider } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  host: z.string().min(1, 'Host is required'),
  port: z.coerce.number().int().min(1).max(65535),
  username: z.string().optional(),
  password: z.string().optional(),
  use_tls: z.boolean().default(true),
});

type FormValues = z.input<typeof schema>;
type FormOutput = z.output<typeof schema>;

const defaults: FormValues = {
  name: '',
  host: '',
  port: 587,
  username: '',
  password: '',
  use_tls: true,
};

export function SmtpProviderForm({ onCreated }: { onCreated: (provider: SmtpProvider) => void }) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues, unknown, FormOutput>({
    resolver: zodResolver(schema),
    defaultValues: defaults,
  });

  const onSubmit = handleSubmit(async (values: FormOutput) => {
    try {
      const provider = await createSmtpProvider(values);
      toast.success('SMTP provider created');
      onCreated(provider);
      reset(defaults);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to create SMTP provider';
      toast.error(message);
    }
  });

  return (
    <Card className="p-6">
      <div className="mb-5 space-y-1">
        <h3 className="text-lg font-semibold">Create SMTP Provider</h3>
        <p className="text-sm text-[var(--muted)]">This form uses React Hook Form + Zod and posts directly to the FastAPI scaffold.</p>
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
          <Field label="Password" error={errors.password?.message}>
            <Input type="password" {...register('password')} placeholder="Stored encrypted on the API side" />
          </Field>
          <label className="flex items-center gap-3 rounded-2xl border border-[var(--card-border)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--foreground)]">
            <input type="checkbox" className="size-4" {...register('use_tls')} />
            Require TLS
          </label>
        </div>
        <Button type="submit" disabled={isSubmitting} className="w-full sm:w-auto">
          {isSubmitting ? <LoaderCircle className="size-4 animate-spin" /> : null}
          {isSubmitting ? 'Saving…' : 'Create provider'}
        </Button>
      </form>
    </Card>
  );
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <label className="space-y-2 text-sm">
      <span className="font-medium">{label}</span>
      {children}
      {error ? <span className="text-xs text-rose-600 dark:text-rose-300">{error}</span> : null}
    </label>
  );
}
