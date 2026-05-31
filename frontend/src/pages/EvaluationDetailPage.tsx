import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import type { Evaluation, Metric, AuditEvent } from "@/types";
import { getEvaluation, getMetric, listAuditEvents } from "@/lib/api";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Spinner } from "@/components/ui/Spinner";
import { MetricCard } from "@/components/MetricCard";
import { AuditTimeline } from "@/components/AuditTimeline";
import { formatDate, shortId, statusVariant } from "@/lib/utils";

interface PageState {
  evaluation: Evaluation;
  metrics: Metric[];
  auditEvents: AuditEvent[];
}

function ProvenanceRow({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt className="text-xs text-muted-foreground py-0.5">{label}</dt>
      <dd className="text-xs font-mono py-0.5">
        <span title={value}>{shortId(value)}…</span>
      </dd>
    </>
  );
}

export function EvaluationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [state, setState] = useState<PageState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setError("Invalid evaluation ID");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);

    void getEvaluation(id)
      .then(async (ev) => {
        const [metrics, auditEvents] = await Promise.all([
          Promise.all(ev.metric_keys.map((k) => getMetric(k))),
          listAuditEvents({ entity_key: ev.id, limit: 50 }),
        ]);
        setState({ evaluation: ev, metrics, auditEvents });
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "Failed to load evaluation");
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex items-center gap-2">
        <Spinner />
        <span className="text-sm text-muted-foreground">Loading…</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-2">
        <p className="text-sm text-danger">{error}</p>
        <Link to="/evaluations" className="text-xs text-primary hover:underline">
          ← Back to Evaluations
        </Link>
      </div>
    );
  }

  if (!state) return null;

  const { evaluation: ev, metrics, auditEvents } = state;
  const metricMap = new Map(metrics.map((m) => [m.entity_key, m]));

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link to="/evaluations" className="text-xs text-muted-foreground hover:underline">
            ← Evaluations
          </Link>
          <h2 className="text-xl font-semibold mt-1">{ev.name}</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            {formatDate(ev.created_at)} · by {ev.created_by}
          </p>
        </div>
        <Badge variant={statusVariant(ev.status)}>
          {ev.status} · {ev.scored_items}/{ev.total_items}
        </Badge>
      </div>

      {/* TRUST FIELD 1–4: Version provenance */}
      <Card>
        <CardHeader>
          <p className="font-medium text-sm">Provenance</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            Exact version IDs locked at evaluation time — fully reproducible
          </p>
        </CardHeader>
        <CardBody>
          <dl className="grid grid-cols-[max-content_1fr] gap-x-8 gap-y-0">
            <ProvenanceRow label="Prompt version" value={ev.prompt_version_id} />
            <ProvenanceRow label="Model version" value={ev.model_version_id} />
            <ProvenanceRow label="Dataset version" value={ev.dataset_version_id} />
            {ev.metric_version_ids.map((vid, i) => (
              <ProvenanceRow key={vid} label={`Metric ${i + 1} version`} value={vid} />
            ))}
          </dl>
        </CardBody>
      </Card>

      {/* TRUST FIELD 5–6: Method + Metric definitions + Confidence */}
      <div>
        <h3 className="font-medium mb-3">
          Metric Results
          <span className="ml-2 text-xs text-muted-foreground font-normal">
            method · definition · confidence
          </span>
        </h3>
        {ev.metric_keys.length === 0 ? (
          <p className="text-sm text-muted-foreground">No metrics attached.</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {ev.metric_keys.map((key, i) => {
              const agg = ev.aggregate_scores[key];
              if (!agg) return null;
              const metric = metricMap.get(key);
              return (
                <MetricCard
                  key={key}
                  metricName={metric?.name ?? agg.metric_name}
                  metricKind={agg.metric_kind}
                  aggregate={agg}
                  versionId={ev.metric_version_ids[i]}
                />
              );
            })}
          </div>
        )}
      </div>

      {/* TRUST FIELD 7: Approval status (stub — Phase 6) */}
      <Card>
        <CardHeader>
          <p className="font-medium text-sm">Approval Status</p>
        </CardHeader>
        <CardBody>
          <div className="flex items-center gap-3">
            <Badge variant="muted">Not configured</Badge>
            <span className="text-xs text-muted-foreground">
              Release gates and human approvals arrive in Phase 6.
            </span>
          </div>
        </CardBody>
      </Card>

      {/* TRUST FIELD 8: Audit history */}
      <div>
        <h3 className="font-medium mb-3">
          Audit History
          <span className="ml-2 text-xs text-muted-foreground font-normal">
            append-only · hash-chained
          </span>
        </h3>
        <AuditTimeline events={auditEvents} />
      </div>
    </div>
  );
}
