import { cva, type VariantProps } from 'class-variance-authority';
import type { ButtonHTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 rounded-2xl text-sm font-medium transition outline-none focus-visible:ring-4 disabled:pointer-events-none disabled:opacity-60',
  {
    variants: {
      variant: {
        default: 'bg-[var(--primary)] px-4 py-2.5 text-[var(--primary-foreground)] hover:opacity-90',
        outline: 'border border-[var(--card-border)] bg-[var(--surface)] px-4 py-2.5 text-[var(--foreground)] hover:bg-black/[0.03] dark:hover:bg-white/5',
        ghost: 'px-3 py-2 text-[var(--muted)] hover:bg-black/[0.04] hover:text-[var(--foreground)] dark:hover:bg-white/5',
      },
      size: {
        default: '',
        icon: 'size-10 px-0 py-0',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
);

export function Button({ className, variant, size, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & VariantProps<typeof buttonVariants>) {
  return <button className={cn(buttonVariants({ variant, size }), className)} {...props} />;
}
