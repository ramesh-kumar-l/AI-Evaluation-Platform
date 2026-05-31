import { Link } from "react-router-dom";
import type { Evaluation } from "@/types";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { formatDate, shortId, statusVariant } from "@/lib/utils";

interface EvaluationCardProps {
  evaluation: Evaluation;
}

export function EvaluationCard({ evaluation: ev }: EvaluationCardProps) {
  return (
    <Link to={`/evaluations/${ev.id}`} className="block">
      <Card className="hover:border-primary/50 transition-colors h-full">
        <CardHeader>
          <div className="flex items-start justify-between gap-2">
            <div>
              <p className="font-medium">{ev.name}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {formatDate(ev.created_at)}
              </p>
            </div>
            <Badge variant={statusVariant(ev.status)}>{ev.status}</Badge>
          </div>
        </CardHeader>
        <CardBody>
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            <dt className="text-muted-foreground">Scored</dt>
            <dd className="font-mono">
              {ev.scored_items}/{ev.total_items} items
            </dd>
            <dt className="text-muted-foreground">Model ver.</dt>
            <dd className="font-mono" title={ev.model_version_id}>
              {shortId(ev.model_version_id)}…
            </dd>
            <dt className="text-muted-foreground">Dataset ver.</dt>
            <dd className="font-mono" title={ev.dataset_version_id}>
              {shortId(ev.dataset_version_id)}…
            </dd>
            <dt className="text-muted-foreground">Metrics</dt>
            <dd className="font-mono">{ev.metric_keys.length}</dd>
          </dl>
        </CardBody>
      </Card>
    </Link>
  );
}
