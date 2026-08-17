'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Boxes, ChevronsLeftRightEllipsis, ContactRound, Gauge, Inbox, LayoutDashboard, Logs, Menu, Settings2 } from 'lucide-react';
import type { ReactNode } from 'react';
import { useMemo, useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { CommandPalette } from '@/components/command-palette';
import { ThemeToggle } from '@/components/theme-toggle';
import { cn } from '@/lib/utils';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/campaigns', label: 'Campaigns', icon: Gauge },
  { href: '/templates', label: 'Templates', icon: Boxes },
  { href: '/contacts', label: 'Contacts', icon: ContactRound },
  { href: '/smtp-providers', label: 'SMTP Providers', icon: ChevronsLeftRightEllipsis },
  { href: '/inbox-checker', label: 'Inbox Checker', icon: Inbox },
  { href: '/logs', label: 'Logs', icon: Logs },
  { href: '/settings', label: 'Settings', icon: Settings2 },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const title = useMemo(
    () => navItems.find((item) => pathname.startsWith(item.href))?.label ?? 'AegisMail Pro',
    [pathname],
  );

  return (
    <div className="flex min-h-screen">
      <aside
        className={cn(
          'sticky top-0 hidden h-screen shrink-0 flex-col border-r border-[var(--sidebar-border)] bg-[var(--sidebar)] px-3 py-4 backdrop-blur xl:flex',
          collapsed ? 'w-[92px]' : 'w-[280px]',
        )}
      >
        <div className="mb-8 flex items-center justify-between gap-3 px-2">
          <div className={cn('overflow-hidden transition-all', collapsed ? 'w-0 opacity-0' : 'w-auto opacity-100')}>
            <p className="text-xs uppercase tracking-[0.3em] text-[var(--muted)]">AegisMail Pro</p>
            <p className="text-lg font-semibold">Phase 1 Console</p>
          </div>
          <Button variant="ghost" size="icon" onClick={() => setCollapsed((value) => !value)} aria-label="Toggle sidebar">
            <Menu className="size-4" />
          </Button>
        </div>
        <nav className="space-y-1">
          {navItems.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  'flex items-center gap-3 rounded-2xl px-3 py-3 text-sm font-medium transition',
                  active ? 'bg-[var(--accent)] text-[var(--accent-foreground)] shadow-sm' : 'text-[var(--muted)] hover:bg-white/60 hover:text-[var(--foreground)] dark:hover:bg-white/6',
                  collapsed && 'justify-center px-2',
                )}
              >
                <Icon className="size-4 shrink-0" />
                {!collapsed && <span>{label}</span>}
              </Link>
            );
          })}
        </nav>
        <div className="mt-auto rounded-3xl border border-[var(--card-border)] bg-[var(--surface-elevated)] p-4 shadow-[var(--shadow)]">
          <Badge variant="success">Scaffold</Badge>
          {!collapsed && (
            <>
              <p className="mt-3 font-medium">Production-minded foundation</p>
              <p className="mt-1 text-sm text-[var(--muted)]">Health checks, metrics, migrations, queue patterns, and a polished app shell are in place.</p>
            </>
          )}
        </div>
      </aside>
      <div className="flex min-h-screen flex-1 flex-col">
        <header className="sticky top-0 z-10 border-b border-[var(--card-border)] bg-[color:var(--surface-elevated)]/90 backdrop-blur">
          <div className="flex items-center justify-between gap-3 px-4 py-4 sm:px-8">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-[var(--muted)]">Enterprise email operations</p>
              <h1 className="text-lg font-semibold">{title}</h1>
            </div>
            <div className="flex items-center gap-3">
              <CommandPalette />
              <ThemeToggle />
            </div>
          </div>
        </header>
        <main className="flex-1 px-4 py-6 sm:px-8 lg:px-10">{children}</main>
      </div>
    </div>
  );
}
