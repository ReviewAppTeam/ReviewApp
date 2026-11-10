import type { QueryStatus } from '@tanstack/react-query';
import { Badge } from '@/components/ui/badge';
import { Card, CardAction, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface ApiStatusProps {
  status: QueryStatus;
}

export function ApiStatus({ status }: ApiStatusProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Backend</CardTitle>
        <CardDescription>FastAPI at /api/v1</CardDescription>
        <CardAction>
          <StatusBadge status={status} />
        </CardAction>
      </CardHeader>
    </Card>
  );
}

function StatusBadge({ status }: ApiStatusProps) {
  switch (status) {
    case 'pending':
      return <Badge variant="secondary">Checking…</Badge>;
    case 'success':
      return <Badge>API is up</Badge>;
    case 'error':
      return <Badge variant="destructive">API is down</Badge>;
  }
}
