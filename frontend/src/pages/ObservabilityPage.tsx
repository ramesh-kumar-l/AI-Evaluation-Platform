import { useState, useEffect } from "react";
import type { Experiment, TrendOut } from "@/types";
import {
  createExperiment,
  listExperiments,
  updateExperiment,
  getMetricTrend,
} from "@/lib/api";
import { SchedulePanel } from "./ObservabilityPanels";

// ---------------------------------------------------------------------------
// TrendsPanel
// ---------------------------------------------------------------------------

function TrendsPanel() {
  const [datasetKey, setDatasetKey] = useState("");
  const [metricKind, setMetricKind] = useState("exact_match");
  const [trend, setTrend] = useState<TrendOut | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleLoad(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const t = await getMetricTrend(datasetKey, metricKind);
      setTrend(t);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load trend");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <h3 className="font-medium text-sm">Quality Trends</h3>
      <form onSubmit={handleLoad} className="flex gap-2 flex-wrap items-end">
        <input className="border rounded px-2 py-1 text-sm font-mono text-xs"
          placeholder="Dataset key (UUID)" value={datasetKey}
          onChange={(e) => setDatasetKey(e.target.value)} required />
        <select className="border rounded px-2 py-1 text-sm" value={metricKind}
          onChange={(e) => setMetricKind(e.target.value)}>
          <option value="exact_match">exact_match</option>
          <option value="contains">contains</option>
          <option value="semantic_similarity">semantic_similarity</option>
        </select>
        <button type="submit" disabled={loading}
          className="bg-primary text-primary-foreground px-3 py-1.5 rounded text-sm">
          {loading ? "Loading…" : "Load Trend"}
        </button>
      </form>
      {error && <p className="text-destructive text-xs">{error}</p>}
      {trend && (
        <div>
          {trend.points.length === 0 ? (
            <p className="text-sm text-muted-foreground">No evaluations found for this dataset.</p>
          ) : (
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="bg-muted text-left">
                  <th className="px-2 py-1 border">Date</th>
                  <th className="px-2 py-1 border">Mean Score</th>
                  <th className="px-2 py-1 border">Eval Status</th>
                </tr>
              </thead>
              <tbody>
                {trend.points.map((p) => (
                  <tr key={p.eval_id} className="border-b">
                    <td className="px-2 py-1 border font-mono">
                      {new Date(p.created_at).toLocaleString()}
                    </td>
                    <td className="px-2 py-1 border font-medium">
                      {(p.mean_score * 100).toFixed(1)}%
                    </td>
                    <td className="px-2 py-1 border text-muted-foreground">{p.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// ExperimentsPanel
// ---------------------------------------------------------------------------

function ExperimentsPanel() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [name, setName] = useState("");
  const [hypothesis, setHypothesis] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  async function load() {
    const exps = await listExperiments();
    setExperiments(exps);
  }

  useEffect(() => { load(); }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCreating(true);
    try {
      const exp = await createExperiment({ name, hypothesis });
      setExperiments((prev) => [exp, ...prev]);
      setName(""); setHypothesis("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed");
    } finally {
      setCreating(false);
    }
  }

  async function conclude(expKey: string) {
    await updateExperiment(expKey, { status: "concluded" });
    load();
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleCreate} className="space-y-2">
        <h3 className="font-medium text-sm">New Experiment</h3>
        {error && <p className="text-destructive text-xs">{error}</p>}
        <input className="w-full border rounded px-2 py-1 text-sm"
          placeholder="Experiment name" value={name}
          onChange={(e) => setName(e.target.value)} required />
        <input className="w-full border rounded px-2 py-1 text-sm"
          placeholder="Hypothesis" value={hypothesis}
          onChange={(e) => setHypothesis(e.target.value)} />
        <button type="submit" disabled={creating}
          className="bg-primary text-primary-foreground px-3 py-1.5 rounded text-sm">
          {creating ? "Creating…" : "Create Experiment"}
        </button>
      </form>

      <div>
        <h3 className="font-medium text-sm mb-2">Experiments</h3>
        {experiments.length === 0 ? (
          <p className="text-sm text-muted-foreground">No experiments yet.</p>
        ) : (
          <div className="space-y-2">
            {experiments.map((exp) => (
              <div key={exp.entity_key} className="border rounded p-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-medium">{exp.name}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    exp.status === "active" ? "bg-blue-100 text-blue-800"
                    : exp.status === "concluded" ? "bg-green-100 text-green-800"
                    : "bg-gray-100 text-gray-600"}`}>
                    {exp.status}
                  </span>
                </div>
                {exp.hypothesis && (
                  <p className="text-xs text-muted-foreground mt-1">
                    H: {exp.hypothesis}
                  </p>
                )}
                {exp.conclusion && (
                  <p className="text-xs mt-1 font-medium">
                    Conclusion: {exp.conclusion}
                  </p>
                )}
                <p className="text-xs text-muted-foreground mt-1">
                  {exp.evaluation_ids.length} evaluations · v{exp.version}
                </p>
                {exp.status === "active" && (
                  <button onClick={() => conclude(exp.entity_key)}
                    className="mt-2 text-xs border rounded px-2 py-1">
                    Mark concluded
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ObservabilityPage
// ---------------------------------------------------------------------------

type Tab = "schedules" | "experiments" | "trends";

export function ObservabilityPage() {
  const [tab, setTab] = useState<Tab>("schedules");

  const tabs: { id: Tab; label: string }[] = [
    { id: "schedules", label: "Schedules" },
    { id: "experiments", label: "Experiments" },
    { id: "trends", label: "Trends" },
  ];

  return (
    <div>
      <h1 className="text-lg font-semibold mb-4">Observability</h1>
      <div className="flex gap-1 mb-6 border-b">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-sm -mb-px border-b-2 transition-colors ${
              tab === t.id
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === "schedules" && <SchedulePanel />}
      {tab === "experiments" && <ExperimentsPanel />}
      {tab === "trends" && <TrendsPanel />}
    </div>
  );
}
