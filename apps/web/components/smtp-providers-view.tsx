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
import { listSmtpProviders } from '@/lib/api';
import type { SmtpProvider } from '@/lib/types';

export function SmtpProvidersView() {
  const [providers, setProviders] = useState<SmtpProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

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

  const tlsCount = useMemo(() => providers.filter((provider) => provider.use_tls).length, [providers]);

  return (
    <div className="grid gap-6 xl:grid-cols-[380px_minmax(0,1fr)]">
      <div className="space-y-6">
        <SmtpProviderForm onCreated={(provider) => setProviders((current) => [provider, ...current])} />
        <Card className="space-y-4 p-6">
          <Badge variant="success">Live API integration</Badge>
          <div className="space-y-1">
            <p className="text-2xl font-semibold">{providers.length}</p>
            <p className="text-sm text-[var(--muted)]">Total provider profiles in the scaffolded API.</p>
          </div>
          <div className="rounded-2xl bg-[var(--accent)] px-4 py-3 text-sm text-[var(--accent-foreground)]">
            {tlsCount} provider{tlsCount === 1 ? '' : 's'} currently marked TLS-enabled.
          </div>
        </Card>
      </div>
      <div className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold">Configured Providers</h3>
            <p className="text-sm text-[var(--muted)]">Includes sorting, filtering, pagination, and column visibility controls.</p>
          </div>
          <Button variant="outline" onClick={() => void refreshProviders()} disabled={refreshing}>
            <RefreshCw className={refreshing ? 'size-4 animate-spin' : 'size-4'} />
            Refresh
          </Button>
        </div>
        {loading ? <SmtpProvidersSkeleton /> : <SmtpProvidersTable data={providers} />}
      </div>
    </div>
  );
}
