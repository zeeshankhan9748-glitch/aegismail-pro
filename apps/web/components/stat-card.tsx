import { Card } from '@/components/ui/card';

export function StatCard({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <Card className="p-6">
      <p className="text-sm text-[var(--muted)]">{label}</p>
      <p className="mt-3 text-2xl font-semibold">{value}</p>
      <p className="mt-2 text-sm text-[var(--muted)]">{detail}</p>
    </Card>
  );
}
