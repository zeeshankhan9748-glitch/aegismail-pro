import { PageHeader } from '@/components/page-header';
import { StatCard } from '@/components/stat-card';

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Executive overview"
        title="Operational confidence, from a single control plane."
        description="Phase 1 focuses on architecture and the first real vertical slice: SMTP provider management, health checks, auth foundations, and queue scaffolding."
      />
      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="API health" value="Healthy" detail="/health and /ready wired" />
        <StatCard label="SMTP providers" value="Live slice" detail="CRUD + stubbed connection test" />
        <StatCard label="Worker pattern" value="Ready" detail="Celery example task with retry/backoff" />
      </div>
    </div>
  );
}
