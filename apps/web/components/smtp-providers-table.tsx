'use client';

import type { ColumnDef } from '@tanstack/react-table';
import { ArrowUpDown, Edit3, PlugZap, ShieldCheck } from 'lucide-react';

import { DataTable } from '@/components/data-table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { SmtpProvider } from '@/lib/types';

type ConnectionResult = {
  success: boolean;
  message: string;
};

type RowData = SmtpProvider & {
  connectionResult?: ConnectionResult;
  isTesting: boolean;
};

export function SmtpProvidersTable({
  data,
  onEdit,
  onTestConnection,
}: {
  data: RowData[];
  onEdit: (provider: SmtpProvider) => void;
  onTestConnection: (providerId: number) => void;
}) {
  const columns: ColumnDef<RowData>[] = [
    {
      accessorKey: 'name',
      header: ({ column }) => (
        <button className="inline-flex items-center gap-2" onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}>
          Name <ArrowUpDown className="size-4" />
        </button>
      ),
    },
    { accessorKey: 'host', header: 'Host' },
    { accessorKey: 'port', header: 'Port' },
    { accessorKey: 'username', header: 'Username' },
    {
      id: 'security',
      header: 'Security',
      cell: ({ row }) => {
        if (row.original.use_ssl) {
          return <Badge variant="success">SSL/TLS</Badge>;
        }
        if (row.original.use_tls) {
          return (
            <Badge variant="success">
              <ShieldCheck className="size-3.5" /> STARTTLS
            </Badge>
          );
        }
        return <Badge variant="outline">None</Badge>;
      },
    },
    { accessorKey: 'throttle_limit_per_minute', header: 'Throttle/min' },
    {
      id: 'connection',
      header: 'Connection',
      cell: ({ row }) =>
        row.original.connectionResult ? (
          <div className="space-y-2">
            <Badge variant={row.original.connectionResult.success ? 'success' : 'destructive'}>
              {row.original.connectionResult.success ? 'Connected' : 'Failed'}
            </Badge>
            <p className="max-w-xs text-xs text-[var(--muted)]">{row.original.connectionResult.message}</p>
          </div>
        ) : (
          <span className="text-sm text-[var(--muted)]">Not tested yet</span>
        ),
    },
    {
      accessorKey: 'created_at',
      header: 'Created',
      cell: ({ row }) => new Date(row.original.created_at).toLocaleDateString(),
    },
    {
      id: 'actions',
      header: 'Actions',
      cell: ({ row }) => (
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" className="px-3 py-2 text-xs" onClick={() => onEdit(row.original)}>
            <Edit3 className="size-4" />
            Edit
          </Button>
          <Button
            type="button"
            variant="outline"
            className="px-3 py-2 text-xs"
            disabled={row.original.isTesting}
            onClick={() => onTestConnection(row.original.id)}
          >
            <PlugZap className="size-4" />
            {row.original.isTesting ? 'Testing…' : 'Test connection'}
          </Button>
        </div>
      ),
    },
  ];

  return <DataTable columns={columns} data={data} filterPlaceholder="Filter providers by name, host, or username…" />;
}
