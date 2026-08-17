import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export function MessagesSkeleton() {
  return (
    <Card className="space-y-4 p-6">
      <Skeleton className="h-10 w-56" />
      <Skeleton className="h-14 w-full" />
      <Skeleton className="h-14 w-full" />
      <Skeleton className="h-14 w-full" />
    </Card>
  );
}
