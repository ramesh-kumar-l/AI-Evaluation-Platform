import React, { useEffect, useState } from "react";
import type { Comparison, GateDecision, ReleaseGate } from "@/types";
import {
  approveDecision,
  createGate,
  evaluateGate,
  listComparisons,
  listGateDecisions,
  listGates,
} from "@/lib/api";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { GateStatusBadge } from "@/components/GateStatusBadge";
import { GateCriteriaResults } from "@/components/GateCriteriaResults";
import { formatDate, shortId } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Gate creation form
// ---------------------------------------------------------------------------

interface CreateFormProps {
  onCreated: (gate: ReleaseGate) => void;
}

function GateCreateForm({ onCreated }: CreateFormProps) {
  const [name, setName] = useState("");
  const [metricKey, setMetricKey] = useState("");
  const [minScore, setMinScore] = useState("0.8");
  const [maxRegressions, setMaxRegressions] = useState("0");
  const [requireApproval, setRequireApproval] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const inputClass =
    "w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary";

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name) return;
    const criteria =
      metricKey.trim()
        ? [{ metric_key: metricKey.trim(), min_score: parseFloat(minScore) }]
        : [];
    setSubmitting(true);
    setError(null);
    void createGate({
      name,
      criteria,
      max_regressions_allowed: parseInt(maxRegressions, 10),
      require_approval: requireApproval,
    })
      .then((g) => {
        onCreated(g);
        setName("");
        setMetricKey("");
      })
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Request failed"),
      )
      .finally(() => setSubmitting(false));
  }

  return (
    <Card>
      <CardHeader>
        <h2 className="text-sm font-semibold">New Release Gate</h2>
      </CardHeader>
      <CardBody>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="mb-1 block text-xs text-muted-foreground">Gate name *</label>
            <input
              className={inputClass}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Production Quality Gate"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Metric key</label>
              <input
                className={inputClass}
                value={metricKey}
                onChange={(e) => setMetricKey(e.target.value)}
                placeholder="e.g. exact_match"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Min score (0–1)</label>
              <input
                className={inputClass}
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={minScore}
                onChange={(e) => setMinScore(e.target.value)}
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">Max regressions</label>
              <input
                className={inputClass}
                type="number"
                min="0"
                value={maxRegressions}
                onChange={(e) => setMaxRegressions(e.target.value)}
              />
            </div>
            <div className="flex items-center gap-2 pt-4">
              <input
                id="require-approval"
                type="checkbox"
                checked={requireApproval}
                onChange={(e) => setRequireApproval(e.target.checked)}
              />
              <label htmlFor="require-approval" className="text-sm">
                Require approval
              </label>
            </div>
          </div>
          {error && <p className="text-xs text-red-600">{error}</p>}
          <button
            type="submit"
            disabled={submitting || !name}
            className="w-full rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {submitting ? "Creating…" : "Create Gate"}
          </button>
        </form>
      </CardBody>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Gate detail: evaluate + decision list + approval
// ---------------------------------------------------------------------------

interface GateDetailProps {
  gate: ReleaseGate;
  comparisons: Comparison[];
}

function GateDetail({ gate, comparisons }: GateDetailProps) {
  const [decisions, setDecisions] = useState<GateDecision[]>([]);
  const [loading, setLoading] = useState(true);
  const [compId, setCompId] = useState("");
  const [evaluating, setEvaluating] = useState(false);
  const [approving, setApproving] = useState<string | null>(null);
  const [justification, setJustification] = useState("");
  const [error, setError] = useState<string | null>(null);

  function loadDecisions() {
    setLoading(true);
    void listGateDecisions(gate.entity_key)
      .then(setDecisions)
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadDecisions();
  }, [gate.entity_key]);

  function handleEvaluate(e: React.FormEvent) {
    e.preventDefault();
    if (!compId) return;
    setEvaluating(true);
    setError(null);
    void evaluateGate(gate.entity_key, compId)
      .then((d) => setDecisions((prev) => [d, ...prev]))
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Evaluation failed"),
      )
      .finally(() => setEvaluating(false));
  }

  function handleApprove(decision: GateDecision, action: string) {
    if (!justification.trim()) return;
    setApproving(decision.id);
    void approveDecision(decision.id, { action, justification })
      .then(() => loadDecisions())
      .catch((err: unknown) =>
        setError(err instanceof Error ? err.message : "Approval failed"),
      )
      .finally(() => setApproving(null));
  }

  const selectClass =
    "w-full rounded-md border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary";

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">{gate.name}</h2>
            <span className="text-xs text-muted-foreground">v{gate.version}</span>
          </div>
        </CardHeader>
        <CardBody className="space-y-3">
          <div className="text-xs text-muted-foreground">
            Max regressions: {gate.max_regressions_allowed} · Requires approval:{" "}
            {gate.require_approval ? "Yes" : "No"}
          </div>
          {gate.criteria.length > 0 && (
            <div>
              <p className="mb-1 text-xs font-medium text-muted-foreground">Criteria</p>
              <table className="w-full text-sm">
                <tbody>
                  {gate.criteria.map((c) => (
                    <tr key={c.metric_key} className="border-b last:border-0">
                      <td className="py-1 pr-4 font-mono text-xs">{c.metric_key}</td>
                      <td className="py-1 text-right">≥ {(c.min_score * 100).toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <form onSubmit={handleEvaluate} className="flex gap-2">
            <select
              className={selectClass}
              value={compId}
              onChange={(e) => setCompId(e.target.value)}
            >
              <option value="">Select comparison to evaluate…</option>
              {comparisons.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} — {c.status} ({shortId(c.id)})
                </option>
              ))}
            </select>
            <button
              type="submit"
              disabled={evaluating || !compId}
              className="whitespace-nowrap rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
            >
              {evaluating ? "…" : "Evaluate"}
            </button>
          </form>
          {error && <p className="text-xs text-red-600">{error}</p>}
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <h3 className="text-sm font-semibold">Decisions ({decisions.length})</h3>
        </CardHeader>
        <CardBody>
          {loading ? (
            <Spinner />
          ) : decisions.length === 0 ? (
            <p className="text-sm text-muted-foreground">No evaluations run yet.</p>
          ) : (
            <div className="space-y-3">
              {decisions.map((d) => (
                <div key={d.id} className="rounded-md border p-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <GateStatusBadge status={d.status} />
                    <span className="text-xs text-muted-foreground">{formatDate(d.created_at)}</span>
                  </div>
                  <GateCriteriaResults criteriaResults={d.criteria_results} />
                  <p className="text-xs text-muted-foreground">
                    Regressions: {d.regressions_detected} / {d.max_regressions_allowed} allowed
                  </p>
                  {(d.status === "pending_approval" || d.status === "failed") && (
                    <div className="space-y-2 pt-1">
                      <textarea
                        className="w-full rounded-md border px-2 py-1 text-sm"
                        rows={2}
                        placeholder="Justification (required, min 10 chars)"
                        value={justification}
                        onChange={(e) => setJustification(e.target.value)}
                      />
                      <div className="flex gap-2">
                        {d.status === "pending_approval" && (
                          <>
                            <button
                              disabled={approving === d.id || justification.length < 10}
                              onClick={() => handleApprove(d, "approved")}
                              className="rounded-md bg-green-600 px-3 py-1 text-xs font-medium text-white disabled:opacity-50"
                            >
                              Approve
                            </button>
                            <button
                              disabled={approving === d.id || justification.length < 10}
                              onClick={() => handleApprove(d, "rejected")}
                              className="rounded-md bg-red-600 px-3 py-1 text-xs font-medium text-white disabled:opacity-50"
                            >
                              Reject
                            </button>
                          </>
                        )}
                        {d.status === "failed" && (
                          <button
                            disabled={approving === d.id || justification.length < 10}
                            onClick={() => handleApprove(d, "overridden")}
                            className="rounded-md bg-amber-600 px-3 py-1 text-xs font-medium text-white disabled:opacity-50"
                          >
                            Override (with justification)
                          </button>
                        )}
                      </div>
                    </div>
                  )}
                  {d.override_justification && (
                    <p className="text-xs italic text-muted-foreground">
                      Override: {d.override_justification}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Root page
// ---------------------------------------------------------------------------

export function GatesPage() {
  const [gates, setGates] = useState<ReleaseGate[]>([]);
  const [comparisons, setComparisons] = useState<Comparison[]>([]);
  const [selected, setSelected] = useState<ReleaseGate | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([listGates(), listComparisons()])
      .then(([g, c]) => {
        setGates(g);
        setComparisons(c);
        if (g.length > 0 && !selected) setSelected(g[0]);
      })
      .finally(() => setLoading(false));
  }, []);

  function handleGateCreated(gate: ReleaseGate) {
    setGates((prev) => [gate, ...prev]);
    setSelected(gate);
  }

  if (loading) return <Spinner />;

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Release Gates</h1>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-4">
          <GateCreateForm onCreated={handleGateCreated} />
          {gates.length > 0 && (
            <Card>
              <CardHeader>
                <h2 className="text-sm font-semibold">Gates ({gates.length})</h2>
              </CardHeader>
              <CardBody>
                <ul className="space-y-1">
                  {gates.map((g) => (
                    <li key={g.entity_key}>
                      <button
                        onClick={() => setSelected(g)}
                        className={`w-full rounded-md px-3 py-2 text-left text-sm transition-colors ${
                          selected?.entity_key === g.entity_key
                            ? "bg-primary/10 font-medium"
                            : "hover:bg-muted"
                        }`}
                      >
                        {g.name}
                        <span className="ml-1 text-xs text-muted-foreground">v{g.version}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              </CardBody>
            </Card>
          )}
        </div>
        <div className="lg:col-span-2">
          {selected ? (
            <GateDetail gate={selected} comparisons={comparisons} />
          ) : (
            <p className="text-sm text-muted-foreground">Create a gate to get started.</p>
          )}
        </div>
      </div>
    </div>
  );
}
