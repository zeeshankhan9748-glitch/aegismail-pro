import { PageHeader } from '@/components/page-header';
import { SmtpProvidersView } from '@/components/smtp-providers-view';

export default function SmtpProvidersPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Configuration"
        title="SMTP Providers"
        description="Create or edit encrypted SMTP provider profiles, test live SMTP connectivity, and prepare providers for Celery-backed message delivery."
      />
      <SmtpProvidersView />
    </div>
  );
}
