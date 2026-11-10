import { useQuery } from '@tanstack/react-query';
import { createFileRoute } from '@tanstack/react-router';
import { healthReadHealthOptions } from '@/api/generated/@tanstack/react-query.gen';
import { ApiStatus } from '@/features/health/api-status';

export const Route = createFileRoute('/')({
  component: HomePage,
});

function HomePage() {
  const health = useQuery(healthReadHealthOptions());

  return (
    <main className="mx-auto flex max-w-2xl flex-col gap-6 p-6">
      <h1 className="font-heading text-2xl font-semibold">ReviewApp</h1>
      <ApiStatus status={health.status} />
    </main>
  );
}
