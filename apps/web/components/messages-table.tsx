'use client';

import type { ColumnDef } from '@tanstack/react-table';
import { ArrowUpDown } from 'lucide-react';
import Link from 'next/link';

import { DataTable } from '@/components/data-table';
import { MessageStatusBadge } from '@/components/message-status-badge';
import { Button } from '@/components/ui/button';
import type { MessageSummary } from '@/lib/types';

const columns: ColumnDef<MessageSummary>[] = [
  {
    accessorKey: 'recipient_email',
    header: ({ column }) => (
      <button className="inline-flex items-center gap-2" onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}>
        Recipient <ArrowUpDown className="size-4" />
      </button>
    ),
  },
  { accessorKey: 'provider_name', header: 'Provider' },
  { accessorKey: 'sender_display_name', header: 'Sender' },
  { accessorKey: 'subject', header: 'Subject' },
  {
    accessorKey: 'status',
    header: 'Status',
    cell: ({ row }) => <MessageStatusBadge status={row.original.status} />,
  },
  { accessorKey: 'attempt_count', header: 'Attempts' },
  {
    accessorKey: 'updated_at',
    header: 'Updated',
    cell: ({ row }) => new Date(row.original.updated_at).toLocaleString(),
  },
  {
    id: 'view',
    header: 'Detail',
    cell: ({ row }) => (
      <Link href={`/messages/${row.original.id}`}>
        <Button type="button" variant="outline" className="px-3 py-2 text-xs">
          View
        </Button>
      </Link>
    ),
  },
];

export function MessagesTable({ data }: { data: MessageSummary[] }) {
  return <DataTable columns={columns} data={data} filterPlaceholder="Filter by recipient, subject, sender, or provider…" />;
}
