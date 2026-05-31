import { useEffect, useState } from "react";
import type { Dataset } from "@/types";
import { listDatasets } from "@/lib/api";
import { Card, CardBody } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { formatDate } from "@/lib/utils";

export function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void listDatasets()
      .then((ds) => setDatasets(ds))
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "Failed to load datasets");
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Datasets</h2>
        <p className="text-sm text-muted-foreground mt-0.5">Versioned evaluation datasets</p>
      </div>

      {loading && (
        <div className="flex items-center gap-2">
          <Spinner />
          <span className="text-sm text-muted-foreground">Loading…</span>
        </div>
      )}

      {error && <p className="text-sm text-danger">{error}</p>}

      {!loading && !error && datasets.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No datasets registered yet. Use{" "}
          <code className="text-xs bg-muted px-1 rounded">POST /datasets</code> to add one.
        </p>
      )}

      {datasets.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {datasets.map((ds) => (
            <Card key={ds.id}>
              <CardBody>
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div>
                    <p className="font-medium text-sm">{ds.name}</p>
                    {ds.description && (
                      <p className="text-xs text-muted-foreground mt-0.5">{ds.description}</p>
                    )}
                  </div>
                  <Badge variant="muted">v{ds.version}</Badge>
                </div>
                <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                  <dt className="text-muted-foreground">Items</dt>
                  <dd className="font-mono">{ds.item_count}</dd>
                  <dt className="text-muted-foreground">Created</dt>
                  <dd>{formatDate(ds.created_at)}</dd>
                  <dt className="text-muted-foreground">By</dt>
                  <dd className="font-mono truncate">{ds.created_by}</dd>
                </dl>
              </CardBody>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
