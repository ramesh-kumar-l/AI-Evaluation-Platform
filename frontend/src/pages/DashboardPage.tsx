import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { Health, Evaluation } from "@/types";
import { getHealth, listEvaluations } from "@/lib/api";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { formatDate, statusVariant } from "@/lib/utils";

export function DashboardPage() {
  const [health, setHealth] = useState<Health | null>(null);
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void Promise.all([getHealth(), listEvaluations()])
      .then(([h, evs]) => {
        setHealth(h);
        setEvaluations(evs.slice(0, 5));
      })
      .catch(() => {
        // API unreachable — health card shows error state
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center gap-2">
        <Spinner />
        <span className="text-sm text-muted-foreground">Loading…</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Dashboard</h2>
        <p className="text-sm text-muted-foreground mt-0.5">Platform overview</p>
      </div>

      <Card>
        <CardHeader>
          <p className="font-medium text-sm">API Health</p>
        </CardHeader>
        <CardBody>
          {health ? (
            <div className="flex flex-wrap items-center gap-3">
              <span className="h-2.5 w-2.5 rounded-full bg-trust" />
              <span className="text-sm">
                {health.status} · v{health.version} · {health.env}
              </span>
              {health.offline_first && <Badge variant="muted">offline-first</Badge>}
            </div>
          ) : (
            <span className="text-sm text-danger">API unreachable</span>
          )}
        </CardBody>
      </Card>

      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-medium">Recent Evaluations</h3>
          <Link to="/evaluations" className="text-xs text-primary hover:underline">
            View all →
          </Link>
        </div>

        {evaluations.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No evaluations yet. Use{" "}
            <code className="text-xs bg-muted px-1 rounded">POST /evaluations</code> to run one.
          </p>
        ) : (
          <div className="space-y-2">
            {evaluations.map((ev) => (
              <Link key={ev.id} to={`/evaluations/${ev.id}`} className="block">
                <Card className="hover:border-primary/50 transition-colors">
                  <CardBody>
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium">{ev.name}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">
                          {formatDate(ev.created_at)}
                        </span>
                        <Badge variant={statusVariant(ev.status)}>{ev.status}</Badge>
                      </div>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {ev.scored_items}/{ev.total_items} items ·{" "}
                      {ev.metric_keys.length} metric
                      {ev.metric_keys.length !== 1 ? "s" : ""}
                    </p>
                  </CardBody>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
