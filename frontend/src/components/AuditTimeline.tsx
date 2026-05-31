import type { AuditEvent } from "@/types";
import { formatDate, shortId } from "@/lib/utils";

interface AuditTimelineProps {
  events: AuditEvent[];
}

export function AuditTimeline({ events }: AuditTimelineProps) {
  if (events.length === 0) {
    return <p className="text-sm text-muted-foreground">No audit events found.</p>;
  }

  return (
    <ol className="relative space-y-4 border-l border-border pl-6">
      {events.map((ev) => (
        <li key={ev.id} className="relative">
          <span className="absolute -left-[1.45rem] flex h-3 w-3 items-center justify-center">
            <span className="h-2 w-2 rounded-full bg-primary" />
          </span>
          <p className="text-xs text-muted-foreground">
            {formatDate(ev.occurred_at)} · seq #{ev.seq}
          </p>
          <div className="mt-0.5 flex flex-wrap items-center gap-2">
            <span className="font-medium text-sm">{ev.action}</span>
            <span className="text-xs text-muted-foreground">{ev.entity_type}</span>
            <span className="text-xs font-mono text-muted-foreground">by {ev.actor}</span>
          </div>
          <p className="mt-1 text-xs font-mono text-muted-foreground">
            <span title={ev.hash}>#{shortId(ev.hash)}</span>
            {ev.prev_hash && (
              <span title={ev.prev_hash}> ← #{shortId(ev.prev_hash)}</span>
            )}
          </p>
        </li>
      ))}
    </ol>
  );
}
