import { useEffect, useState } from "react";
import type { Evaluation } from "@/types";
import { listEvaluations } from "@/lib/api";
import { EvaluationCard } from "@/components/EvaluationCard";
import { Spinner } from "@/components/ui/Spinner";

export function EvaluationsPage() {
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void listEvaluations()
      .then((evs) => setEvaluations(evs))
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "Failed to load evaluations");
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Evaluations</h2>
        <p className="text-sm text-muted-foreground mt-0.5">
          Dataset-level runs with scored, trust-annotated results
        </p>
      </div>

      {loading && (
        <div className="flex items-center gap-2">
          <Spinner />
          <span className="text-sm text-muted-foreground">Loading…</span>
        </div>
      )}

      {error && <p className="text-sm text-danger">{error}</p>}

      {!loading && !error && evaluations.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No evaluations found. Use{" "}
          <code className="text-xs bg-muted px-1 rounded">POST /evaluations</code> to run one.
        </p>
      )}

      {evaluations.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {evaluations.map((ev) => (
            <EvaluationCard key={ev.id} evaluation={ev} />
          ))}
        </div>
      )}
    </div>
  );
}
