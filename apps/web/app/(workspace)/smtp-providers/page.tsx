import { PageHeader } from '@/components/page-header';
import { SmtpProvidersView } from '@/components/smtp-providers-view';

export default function SmtpProvidersPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Configuration"
        title="SMTP Providers"
        description="A working Phase 1 slice backed by the FastAPI scaffold. Create provider profiles, inspect stored records, and validate the end-to-end shape for future sending workflows."
      />
      <SmtpProvidersView />
    </div>
  );
}
