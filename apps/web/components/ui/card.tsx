import type { HTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('rounded-[28px] border border-[var(--card-border)] bg-[var(--card)] backdrop-blur shadow-[var(--shadow)]', className)}
      {...props}
    />
  );
}
