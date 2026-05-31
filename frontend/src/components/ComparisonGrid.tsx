import React from "react";
import type { MetricDelta } from "@/types";
import { Badge } from "@/components/ui/Badge";
import { formatScore } from "@/lib/utils";

interface ComparisonGridProps {
  metricDeltas: Record<string, MetricDelta>;
}

function DeltaCell({ delta }: { delta: number }) {
  const sign = delta > 0 ? "+" : "";
  const variant = delta < 0 ? "danger" : delta > 0 ? "trust" : "muted";
  return (
    <Badge variant={variant} className="font-mono text-xs">
      {sign}{(delta * 100).toFixed(1)}pp
    </Badge>
  );
}

export function ComparisonGrid({ metricDeltas }: ComparisonGridProps) {
  const entries = Object.entries(metricDeltas);
  if (entries.length === 0) {
    return <p className="text-sm text-muted-foreground">No shared metrics between these evaluations.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-xs text-muted-foreground">
            <th className="py-2 pr-4 text-left font-medium">Metric</th>
            <th className="py-2 pr-4 text-right font-medium">Baseline</th>
            <th className="py-2 pr-4 text-right font-medium">Candidate</th>
            <th className="py-2 pr-4 text-right font-medium">Delta</th>
            <th className="py-2 text-left font-medium">Verdict</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(([metricKey, d]) => (
            <tr key={metricKey} className="border-b last:border-0">
              <td className="py-2 pr-4">
                <div className="font-medium">{d.metric_name}</div>
                <div className="text-xs text-muted-foreground">{d.metric_kind}</div>
              </td>
              <td className="py-2 pr-4 text-right font-mono">{formatScore(d.baseline_score)}</td>
              <td className="py-2 pr-4 text-right font-mono">{formatScore(d.candidate_score)}</td>
              <td className="py-2 pr-4 text-right">
                <DeltaCell delta={d.delta} />
              </td>
              <td className="py-2">
                {d.regression && <Badge variant="danger">Regression</Badge>}
                {d.improvement && <Badge variant="trust">Improvement</Badge>}
                {!d.regression && !d.improvement && <Badge variant="muted">Neutral</Badge>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
