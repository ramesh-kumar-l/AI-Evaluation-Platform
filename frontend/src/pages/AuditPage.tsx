import { useEffect, useState } from "react";
import type { AuditEvent } from "@/types";
import { listAuditEvents } from "@/lib/api";
import { AuditTimeline } from "@/components/AuditTimeline";
import { Spinner } from "@/components/ui/Spinner";

export function AuditPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void listAuditEvents({ limit: 100 })
      .then((evs) => setEvents(evs))
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "Failed to load audit events");
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold">Audit Trail</h2>
        <p className="text-sm text-muted-foreground mt-0.5">
          Append-only, hash-chained record of every mutation
        </p>
      </div>

      {loading && (
        <div className="flex items-center gap-2">
          <Spinner />
          <span className="text-sm text-muted-foreground">Loading…</span>
        </div>
      )}

      {error && <p className="text-sm text-danger">{error}</p>}

      {!loading && !error && <AuditTimeline events={events} />}
    </div>
  );
}
