import type { AggregateScore } from "@/types";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { TrustIndicator } from "@/components/TrustIndicator";
import { formatScore, scoreColor, shortId } from "@/lib/utils";

interface MetricCardProps {
  metricName: string;
  metricKind: string;
  aggregate: AggregateScore;
  versionId?: string;
}

const KIND_LABELS: Record<string, string> = {
  exact_match: "Exact Match",
  contains: "Contains",
  semantic_similarity: "Semantic Similarity",
};

export function MetricCard({ metricName, metricKind, aggregate, versionId }: MetricCardProps) {
  const dist = aggregate.confidence_distribution;
  const dominantConfidence =
    Object.entries(dist).sort(([, a], [, b]) => (b ?? 0) - (a ?? 0))[0]?.[0] ?? "low";

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-2">
          <div>
            <p className="font-medium">{metricName}</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              {KIND_LABELS[metricKind] ?? metricKind}
              {versionId && (
                <span className="ml-2 font-mono opacity-60" title={versionId}>
                  v:{shortId(versionId)}
                </span>
              )}
            </p>
          </div>
          <span className={`text-2xl font-bold tabular-nums ${scoreColor(aggregate.mean_score)}`}>
            {formatScore(aggregate.mean_score)}
          </span>
        </div>
      </CardHeader>
      <CardBody>
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-xs text-muted-foreground">
            {aggregate.count} item{aggregate.count !== 1 ? "s" : ""}
          </span>
          <TrustIndicator confidence={dominantConfidence} />
          <div className="flex gap-1 flex-wrap">
            {(["high", "medium", "low"] as const).map((level) => {
              const count = dist[level];
              if (!count) return null;
              return (
                <Badge
                  key={level}
                  variant={level === "high" ? "trust" : level === "medium" ? "warning" : "muted"}
                >
                  {count} {level}
                </Badge>
              );
            })}
          </div>
        </div>
      </CardBody>
    </Card>
  );
}
