import type { Metadata } from 'next';
import { Toaster } from 'sonner';

import { AppProviders } from '@/components/app-providers';
import './globals.css';

export const metadata: Metadata = {
  title: 'AegisMail Pro',
  description: 'Phase 1 scaffold for enterprise email operations.',
};

export default function RootLayout({ children }: LayoutProps<'/'>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground antialiased">
        <AppProviders>
          {children}
          <Toaster richColors position="top-right" />
        </AppProviders>
      </body>
    </html>
  );
}
