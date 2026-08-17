import { forwardRef, type InputHTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn(
        'h-11 w-full rounded-2xl border border-[var(--card-border)] bg-[var(--surface)] px-4 text-sm outline-none focus:ring-4 focus:ring-[var(--ring)]',
        className,
      )}
      {...props}
    />
  ),
);

Input.displayName = 'Input';
