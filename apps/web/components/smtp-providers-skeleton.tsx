import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export function SmtpProvidersSkeleton() {
  return (
    <Card className="space-y-4 p-6">
      <div className="flex items-center justify-between gap-3">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-10 w-32" />
      </div>
      <Skeleton className="h-12 w-full" />
      <Skeleton className="h-12 w-full" />
      <Skeleton className="h-12 w-full" />
    </Card>
  );
}
