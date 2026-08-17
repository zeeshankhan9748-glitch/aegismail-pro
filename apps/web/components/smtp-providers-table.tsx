'use client';

import type { ColumnDef } from '@tanstack/react-table';
import { ArrowUpDown, ShieldCheck } from 'lucide-react';

import { DataTable } from '@/components/data-table';
import { Badge } from '@/components/ui/badge';
import type { SmtpProvider } from '@/lib/types';

const columns: ColumnDef<SmtpProvider>[] = [
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
    accessorKey: 'use_tls',
    header: 'Security',
    cell: ({ row }) =>
      row.original.use_tls ? (
        <Badge variant="success">
          <ShieldCheck className="size-3.5" /> TLS
        </Badge>
      ) : (
        <Badge variant="outline">Plain</Badge>
      ),
  },
  {
    accessorKey: 'created_at',
    header: 'Created',
    cell: ({ row }) => new Date(row.original.created_at).toLocaleDateString(),
  },
];

export function SmtpProvidersTable({ data }: { data: SmtpProvider[] }) {
  return <DataTable columns={columns} data={data} filterPlaceholder="Filter providers by name, host, or username…" />;
}
