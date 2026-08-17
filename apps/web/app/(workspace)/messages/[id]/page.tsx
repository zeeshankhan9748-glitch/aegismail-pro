import { MessageDetailView } from '@/components/message-detail-view';

export default async function MessageDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <MessageDetailView messageId={Number(id)} />;
}
