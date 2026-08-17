'use client';

import { Command } from 'cmdk';
import { useRouter } from 'next/navigation';
import { CommandIcon } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';

const actions = [
  { label: 'Open SMTP Providers', description: 'Jump to the live CRUD slice', href: '/smtp-providers' },
  { label: 'Visit Dashboard', description: 'Return to the overview', href: '/dashboard' },
];

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setOpen((value) => !value);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  return (
    <>
      <Button variant="outline" onClick={() => setOpen(true)} className="gap-2">
        <CommandIcon className="size-4" />
        <span className="hidden sm:inline">Command palette</span>
        <span className="rounded-md border border-[var(--card-border)] px-1.5 py-0.5 text-xs text-[var(--muted)]">⌘K</span>
      </Button>
      {open ? (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-slate-950/35 px-4 py-24 backdrop-blur-sm" onClick={() => setOpen(false)}>
          <Command className="w-full max-w-2xl overflow-hidden rounded-3xl border border-[var(--card-border)] bg-[var(--surface)] p-3 shadow-[var(--shadow)]" onClick={(event) => event.stopPropagation()}>
            <Command.Input className="w-full rounded-2xl border border-[var(--card-border)] bg-transparent px-4 py-3 outline-none" placeholder="Search commands…" />
            <Command.List className="mt-3 max-h-72 overflow-auto">
              <Command.Empty className="px-4 py-8 text-sm text-[var(--muted)]">No matching actions.</Command.Empty>
              <Command.Group heading="Quick actions" className="text-sm text-[var(--muted)]">
                {actions.map((action) => (
                  <Command.Item
                    key={action.href}
                    className="cursor-pointer rounded-2xl px-4 py-3 outline-none data-[selected=true]:bg-[var(--accent)]"
                    onSelect={() => {
                      router.push(action.href);
                      setOpen(false);
                    }}
                  >
                    <div>
                      <p className="font-medium text-[var(--foreground)]">{action.label}</p>
                      <p className="text-sm text-[var(--muted)]">{action.description}</p>
                    </div>
                  </Command.Item>
                ))}
              </Command.Group>
            </Command.List>
          </Command>
        </div>
      ) : null}
    </>
  );
}
