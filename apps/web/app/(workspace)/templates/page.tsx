import { PageHeader } from '@/components/page-header';
import { TemplatesView } from '@/components/templates-view';

export default function TemplatesPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="AegisMail Pro"
        title="Templates"
        description="Build reusable email templates with {{placeholder}} variables, live preview, and version history."
      />
      <TemplatesView />
    </div>
  );
}
