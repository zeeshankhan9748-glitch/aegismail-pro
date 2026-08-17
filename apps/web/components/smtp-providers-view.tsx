'use client';

import { RefreshCw } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { toast } from 'sonner';

import { SmtpProviderForm } from '@/components/smtp-provider-form';
import { SmtpProvidersSkeleton } from '@/components/smtp-providers-skeleton';
import { SmtpProvidersTable } from '@/components/smtp-providers-table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { listSmtpProviders, testSmtpProviderConnection } from '@/lib/api';
import type { SmtpProvider } from '@/lib/types';

type ConnectionState = Record<number, { success: boolean; message: string }>;

export function SmtpProvidersView() {
  const [providers, setProviders] = useState<SmtpProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [editingProvider, setEditingProvider] = useState<SmtpProvider | null>(null);
  const [testingProviderId, setTestingProviderId] = useState<number | null>(null);
  const [connectionStates, setConnectionStates] = useState<ConnectionState>({});

  const loadProviders = useCallback(async () => {
    return listSmtpProviders();
  }, []);

  const refreshProviders = useCallback(async () => {
    try {
      setRefreshing(true);
      const rows = await loadProviders();
      setProviders(rows);
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to fetch SMTP providers';
      toast.error(message);
    } finally {
      setRefreshing(false);
    }
  }, [loadProviders]);

  useEffect(() => {
    let active = true;

    const fetchInitialProviders = async () => {
      try {
        const rows = await loadProviders();
        if (active) {
          setProviders(rows);
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Unable to fetch SMTP providers';
        toast.error(message);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    void fetchInitialProviders();

    return () => {
      active = false;
    };
  }, [loadProviders]);

  const tlsCount = useMemo(() => providers.filter((provider) => provider.use_tls || provider.use_ssl).length, [providers]);

  const tableData = useMemo(
    () =>
      providers.map((provider) => ({
        ...provider,
        connectionResult: connectionStates[provider.id],
        isTesting: testingProviderId === provider.id,
      })),
    [connectionStates, providers, testingProviderId],
  );

  const handleTestConnection = useCallback(async (providerId: number) => {
    try {
      setTestingProviderId(providerId);
      const result = await testSmtpProviderConnection(providerId);
      setConnectionStates((current) => ({
        ...current,
        [providerId]: { success: result.success, message: result.message },
      }));
      if (result.success) {
        toast.success('SMTP connection successful');
      } else {
        toast.error(result.message);
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to test SMTP connection';
      toast.error(message);
      setConnectionStates((current) => ({
        ...current,
        [providerId]: { success: false, message },
      }));
    } finally {
      setTestingProviderId(null);
    }
  }, []);

  return (
    <div className="grid gap-6 xl:grid-cols-[380px_minmax(0,1fr)]">
      <div className="space-y-6">
        <SmtpProviderForm
          editingProvider={editingProvider}
          onCreated={(provider) => {
            setProviders((current) => [provider, ...current]);
          }}
          onUpdated={(provider) => {
            setProviders((current) => current.map((item) => (item.id === provider.id ? provider : item)));
          }}
          onCancelEdit={() => setEditingProvider(null)}
        />
        <Card className="space-y-4 p-6">
          <Badge variant="success">Live SMTP controls</Badge>
          <div className="space-y-1">
            <p className="text-2xl font-semibold">{providers.length}</p>
            <p className="text-sm text-[var(--muted)]">Provider profiles ready for real connection tests and Celery-backed sends.</p>
          </div>
          <div className="rounded-2xl bg-[var(--accent)] px-4 py-3 text-sm text-[var(--accent-foreground)]">
            {tlsCount} provider{tlsCount === 1 ? '' : 's'} currently using STARTTLS or SSL/TLS.
          </div>
        </Card>
      </div>
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold">Configured Providers</h3>
            <p className="text-sm text-[var(--muted)]">Edit provider settings, run a real test connection, and inspect the latest connection result inline.</p>
          </div>
          <Button variant="outline" onClick={() => void refreshProviders()} disabled={refreshing}>
            <RefreshCw className={refreshing ? 'size-4 animate-spin' : 'size-4'} />
            Refresh
          </Button>
        </div>
        {loading ? (
          <SmtpProvidersSkeleton />
        ) : (
          <SmtpProvidersTable data={tableData} onEdit={setEditingProvider} onTestConnection={handleTestConnection} />
        )}
      </div>
    </div>
  );
}
