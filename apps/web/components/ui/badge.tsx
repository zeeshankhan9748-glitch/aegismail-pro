import type { HTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

export function Badge({ className, variant = 'default', ...props }: HTMLAttributes<HTMLSpanElement> & { variant?: 'default' | 'outline' | 'success' }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium',
        variant === 'default' && 'bg-[var(--foreground)]/10 text-[var(--foreground)]',
        variant === 'outline' && 'border border-[var(--card-border)] text-[var(--muted)]',
        variant === 'success' && 'bg-[var(--success-surface)] text-[var(--success)]',
        className,
      )}
      {...props}
    />
  );
}
