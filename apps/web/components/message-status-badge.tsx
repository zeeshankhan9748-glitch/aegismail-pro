'use client';

import { Badge } from '@/components/ui/badge';
import type { Message } from '@/lib/types';

export function MessageStatusBadge({ status }: { status: Message['status'] }) {
  if (status === 'sent') {
    return <Badge variant="success">Sent</Badge>;
  }
  if (status === 'failed') {
    return <Badge variant="destructive">Failed</Badge>;
  }
  if (status === 'deferred') {
    return <Badge variant="warning">Deferred</Badge>;
  }
  if (status === 'processing') {
    return <Badge variant="default">Processing</Badge>;
  }
  return <Badge variant="outline">Queued</Badge>;
}
