import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import type { Comparison, Evaluation } from "@/types";
import { createComparison, getComparison, listComparisons, listEvaluations } from "@/lib/api";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { RegressionBadge } from "@/components/RegressionBadge";
import { ComparisonGrid } from "@/components/ComparisonGrid";
import { shortId, formatDate } from "@/lib/utils";

// ---------------------------------------------------------------------------
// New comparison form
// ---------------------------------------------------------------------------

interface CompareFormProps {
  evaluations: Evaluation[];
  onCreated: (comp: Comparison) => void;
}

function CompareForm({ evaluations, onCreated }: CompareFormProps) {
  const [baselineId, setBaselineId] = useState("");
  const [candidateId, setCandidateId] = useState("");
  const [kind, setKind] = useState("generic");
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!baselineId || !candidateId) return;
    setSubmitting(true);
    setError(null);
    void createComparison({ name: name || "Comparison", baseline_id: baselineId, candidate_id: candidateId, kind })
      .then(onCreated)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Request failed"))
      .finally(() => setSubmitting(false));
  }

  const selectClass = "w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary";

  return (
    <Card>
      <CardHeader>
        <h2 className="text-sm font-semibold">New Comparison</h2>
      </CardHeader>
      <CardBody>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="mb-1 block text-xs text-muted-foreground">Name (optional)</label>
            <input
              className={selectClass}
              placeholder="e.g. llama3 vs mistral on qa-v2"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Baseline evaluation</label>
              <select className={selectClass} value={baselineId} onChange={(e) => setBaselineId(e.target.value)} required>
                <option value="">Select…</option>
                {evaluations.map((ev) => (
                  <option key={ev.id} value={ev.id}>{ev.name} ({shortId(ev.id)})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Candidate evaluation</label>
              <select className={selectClass} value={candidateId} onChange={(e) => setCandidateId(e.target.value)} required>
                <option value="">Select…</option>
                {evaluations.map((ev) => (
                  <option key={ev.id} value={ev.id}>{ev.name} ({shortId(ev.id)})</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="mb-1 block text-xs text-muted-foreground">Comparison kind</label>
            <select className={selectClass} value={kind} onChange={(e) => setKind(e.target.value)}>
              <option value="generic">Generic</option>
              <option value="model">Model vs model</option>
              <option value="prompt">Prompt vs prompt</option>
              <option value="dataset">Dataset version</option>
            </select>
          </div>
          {error && <p className="text-xs text-danger">{error}</p>}
          <button
            type="submit"
            disabled={submitting || !baselineId || !candidateId}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {submitting ? "Running…" : "Run comparison"}
          </button>
        </form>
      </CardBody>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Comparison result detail
// ---------------------------------------------------------------------------

interface ComparisonDetailProps {
  compId: string;
}

function ComparisonDetail({ compId }: ComparisonDetailProps) {
  const [comp, setComp] = useState<Comparison | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void getComparison(compId)
      .then(setComp)
      .finally(() => setLoading(false));
  }, [compId]);

  if (loading) return <Spinner className="mt-4" />;
  if (!comp) return <p className="text-sm text-muted-foreground">Comparison not found.</p>;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold">{comp.name}</h2>
          <RegressionBadge
            status={comp.status}
            count={comp.status === "regression" ? comp.regressions_detected : comp.improvements_detected}
          />
        </div>
        <div className="mt-1 flex gap-4 text-xs text-muted-foreground">
          <span>Kind: {comp.kind}</span>
          <span>Baseline: <Link to={`/evaluations/${comp.baseline_id}`} className="underline">{shortId(comp.baseline_id)}</Link></span>
          <span>Candidate: <Link to={`/evaluations/${comp.candidate_id}`} className="underline">{shortId(comp.candidate_id)}</Link></span>
          <span>{formatDate(comp.created_at)}</span>
        </div>
      </CardHeader>
      <CardBody>
        <ComparisonGrid metricDeltas={comp.metric_deltas} />
        {comp.notes && <p className="mt-3 text-xs text-muted-foreground">{comp.notes}</p>}
      </CardBody>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Comparison history list
// ---------------------------------------------------------------------------

interface ComparisonHistoryProps {
  comparisons: Comparison[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

function ComparisonHistory({ comparisons, selectedId, onSelect }: ComparisonHistoryProps) {
  if (comparisons.length === 0) {
    return <p className="text-sm text-muted-foreground">No comparisons yet.</p>;
  }
  return (
    <ul className="space-y-1">
      {comparisons.map((c) => (
        <li key={c.id}>
          <button
            onClick={() => onSelect(c.id)}
            className={`w-full rounded-md px-3 py-2 text-left text-sm transition-colors ${
              selectedId === c.id ? "bg-primary/10 font-medium" : "hover:bg-muted"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="truncate">{c.name}</span>
              <RegressionBadge status={c.status} />
            </div>
            <div className="text-xs text-muted-foreground">{formatDate(c.created_at)}</div>
          </button>
        </li>
      ))}
    </ul>
  );
}

// ---------------------------------------------------------------------------
// Page root
// ---------------------------------------------------------------------------

export function ComparePage() {
  const [evaluations, setEvaluations] = useState<Evaluation[]>([]);
  const [comparisons, setComparisons] = useState<Comparison[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void Promise.all([listEvaluations(), listComparisons()])
      .then(([evs, comps]) => { setEvaluations(evs); setComparisons(comps); })
      .finally(() => setLoading(false));
  }, []);

  function handleCreated(comp: Comparison) {
    setComparisons((prev) => [comp, ...prev]);
    setSelectedId(comp.id);
  }

  if (loading) return <div className="flex justify-center pt-16"><Spinner /></div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold">Compare Evaluations</h1>
        <p className="text-sm text-muted-foreground">Detect regressions and improvements across evaluations on the same dataset.</p>
      </div>

      <CompareForm evaluations={evaluations} onCreated={handleCreated} />

      <div className="grid grid-cols-[240px_1fr] gap-4">
        <div>
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">History</h2>
          <ComparisonHistory comparisons={comparisons} selectedId={selectedId} onSelect={setSelectedId} />
        </div>
        <div>
          {selectedId ? (
            <ComparisonDetail key={selectedId} compId={selectedId} />
          ) : (
            <div className="flex h-32 items-center justify-center rounded-lg border border-dashed">
              <p className="text-sm text-muted-foreground">Select a comparison to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
