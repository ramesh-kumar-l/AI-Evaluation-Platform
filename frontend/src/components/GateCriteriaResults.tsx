import type { CriterionResult } from "@/types";

interface Props {
  criteriaResults: Record<string, CriterionResult>;
}

export function GateCriteriaResults({ criteriaResults }: Props) {
  const entries = Object.values(criteriaResults);

  if (entries.length === 0) {
    return <p className="text-sm text-muted-foreground">No criteria defined for this gate.</p>;
  }

  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b text-left text-muted-foreground">
          <th className="py-1 pr-4 font-medium">Metric</th>
          <th className="py-1 pr-4 font-medium text-right">Required</th>
          <th className="py-1 pr-4 font-medium text-right">Actual</th>
          <th className="py-1 font-medium text-right">Result</th>
        </tr>
      </thead>
      <tbody>
        {entries.map((r) => (
          <tr key={r.metric_key} className="border-b last:border-0">
            <td className="py-1 pr-4 font-mono text-xs">{r.metric_key}</td>
            <td className="py-1 pr-4 text-right">{(r.min_score * 100).toFixed(0)}%</td>
            <td className="py-1 pr-4 text-right">{(r.candidate_score * 100).toFixed(1)}%</td>
            <td className="py-1 text-right">
              {r.passed ? (
                <span className="font-semibold text-green-600">Pass</span>
              ) : (
                <span className="font-semibold text-red-600">Fail</span>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
