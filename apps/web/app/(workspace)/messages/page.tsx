import { MessagesView } from '@/components/messages-view';
import { PageHeader } from '@/components/page-header';

export default function MessagesPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Delivery"
        title="Messages"
        description="Create sender identities, queue one-off SMTP sends, and inspect message status transitions backed by the FastAPI API and Celery worker."
      />
      <MessagesView />
    </div>
  );
}
