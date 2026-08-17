import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';

export function PlaceholderPage({ title, description }: { title: string; description: string }) {
  return (
    <div className="space-y-6">
      <div>
        <Badge variant="outline">Planned module</Badge>
        <h2 className="mt-4 text-3xl font-semibold">{title}</h2>
        <p className="mt-3 max-w-3xl text-[var(--muted)]">{description}</p>
      </div>
      <Card className="p-8">
        <p className="text-sm text-[var(--muted)]">
          This route is intentionally scaffolded now so later phases can add full behavior without reworking navigation, layout, or information architecture.
        </p>
      </Card>
    </div>
  );
}
