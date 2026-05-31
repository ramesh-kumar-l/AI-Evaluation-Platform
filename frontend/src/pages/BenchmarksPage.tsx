import { useEffect, useState } from "react";
import type { Benchmark, DatasetPolicy, Dataset } from "@/types";
import {
  createBenchmark,
  listBenchmarks,
  setBenchmarkStatus,
  upsertDatasetPolicy,
  getDatasetPolicy,
  listDatasets,
} from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const STATUS_VARIANT: Record<string, "trust" | "warning" | "danger" | "muted"> = {
  draft: "muted",
  active: "trust",
  deprecated: "warning",
  archived: "danger",
};

const LIFECYCLE_TRANSITIONS: Record<string, string[]> = {
  draft: ["active", "deprecated"],
  active: ["deprecated"],
  deprecated: ["archived"],
  archived: [],
};

// ---------------------------------------------------------------------------
// BenchmarkCreateForm
// ---------------------------------------------------------------------------

interface CreateFormProps {
  datasets: Dataset[];
  onCreated: (b: Benchmark) => void;
}

function BenchmarkCreateForm({ datasets, onCreated }: CreateFormProps) {
  const [name, setName] = useState("");
  const [domain, setDomain] = useState("");
  const [taskType, setTaskType] = useState("");
  const [datasetKey, setDatasetKey] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const b = await createBenchmark({
        name,
        domain,
        task_type: taskType,
        dataset_key: datasetKey || null,
      });
      setName("");
      setDomain("");
      setTaskType("");
      setDatasetKey("");
      onCreated(b);
    } catch (err) {
      setError(String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card>
      <div className="p-4 border-b">
        <h2 className="text-sm font-semibold">New Benchmark</h2>
      </div>
      <form onSubmit={handleSubmit} className="p-4 space-y-3">
        <div>
          <label className="text-xs font-medium text-muted-foreground">Name *</label>
          <input
            className="mt-1 w-full rounded border px-3 py-1.5 text-sm"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="MMLU, HellaSwag…"
            required
          />
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground">Domain</label>
          <input
            className="mt-1 w-full rounded border px-3 py-1.5 text-sm"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            placeholder="nlp, vision, code…"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground">Task Type</label>
          <input
            className="mt-1 w-full rounded border px-3 py-1.5 text-sm"
            value={taskType}
            onChange={(e) => setTaskType(e.target.value)}
            placeholder="qa, classification, summarisation…"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground">Dataset (optional)</label>
          <select
            className="mt-1 w-full rounded border px-3 py-1.5 text-sm"
            value={datasetKey}
            onChange={(e) => setDatasetKey(e.target.value)}
          >
            <option value="">— none —</option>
            {datasets.map((d) => (
              <option key={d.entity_key} value={d.entity_key}>
                {d.name}
              </option>
            ))}
          </select>
        </div>
        {error && <p className="text-xs text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={submitting || !name.trim()}
          className="w-full rounded bg-primary px-3 py-1.5 text-sm text-primary-foreground disabled:opacity-50"
        >
          {submitting ? "Creating…" : "Create Benchmark"}
        </button>
      </form>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// DatasetPolicyPanel
// ---------------------------------------------------------------------------

interface PolicyPanelProps {
  datasetKey: string;
}

function DatasetPolicyPanel({ datasetKey }: PolicyPanelProps) {
  const [policy, setPolicy] = useState<DatasetPolicy | null>(null);
  const [owner, setOwner] = useState("system");
  const [status, setStatus] = useState("active");
  const [saving, setSaving] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    getDatasetPolicy(datasetKey)
      .then((p) => {
        setPolicy(p);
        setOwner(p.owner);
        setStatus(p.status);
      })
      .catch(() => {
        /* no policy yet */
      })
      .finally(() => setLoaded(true));
  }, [datasetKey]);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const p = await upsertDatasetPolicy(datasetKey, { owner, status });
      setPolicy(p);
    } finally {
      setSaving(false);
    }
  }

  if (!loaded) return <Spinner />;

  return (
    <div className="mt-4 border-t pt-4">
      <h3 className="text-xs font-semibold text-muted-foreground uppercase mb-2">
        Dataset Policy
      </h3>
      {policy && (
        <div className="mb-2 text-xs text-muted-foreground">
          Owner: <span className="font-medium text-foreground">{policy.owner}</span> · Status:{" "}
          <Badge variant={STATUS_VARIANT[policy.status] ?? "muted"}>{policy.status}</Badge>
        </div>
      )}
      <form onSubmit={handleSave} className="flex gap-2 items-end">
        <div className="flex-1">
          <input
            className="w-full rounded border px-2 py-1 text-xs"
            placeholder="Owner"
            value={owner}
            onChange={(e) => setOwner(e.target.value)}
          />
        </div>
        <select
          className="rounded border px-2 py-1 text-xs"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          {["active", "deprecated", "archived"].map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <button
          type="submit"
          disabled={saving}
          className="rounded bg-primary px-3 py-1 text-xs text-primary-foreground disabled:opacity-50"
        >
          {saving ? "Saving…" : policy ? "Update" : "Create"}
        </button>
      </form>
    </div>
  );
}

// ---------------------------------------------------------------------------
// BenchmarkDetail
// ---------------------------------------------------------------------------

interface DetailProps {
  benchmark: Benchmark;
  onUpdated: (b: Benchmark) => void;
}

function BenchmarkDetail({ benchmark, onUpdated }: DetailProps) {
  const [transitioning, setTransitioning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const transitions = LIFECYCLE_TRANSITIONS[benchmark.status] ?? [];

  async function handleTransition(newStatus: string) {
    setTransitioning(true);
    setError(null);
    try {
      const updated = await setBenchmarkStatus(benchmark.entity_key, { status: newStatus });
      onUpdated(updated);
    } catch (err) {
      setError(String(err));
    } finally {
      setTransitioning(false);
    }
  }

  return (
    <Card>
      <div className="p-4 border-b flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold">{benchmark.name}</h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            v{benchmark.version} · key {benchmark.entity_key.slice(0, 8)}
          </p>
        </div>
        <Badge variant={STATUS_VARIANT[benchmark.status] ?? "muted"}>{benchmark.status}</Badge>
      </div>

      <div className="p-4 space-y-2 text-sm">
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
          <span className="text-muted-foreground">Domain</span>
          <span>{benchmark.domain || "—"}</span>
          <span className="text-muted-foreground">Task type</span>
          <span>{benchmark.task_type || "—"}</span>
          <span className="text-muted-foreground">Metric keys</span>
          <span>{benchmark.metric_keys.length > 0 ? benchmark.metric_keys.join(", ") : "—"}</span>
          <span className="text-muted-foreground">Dataset key</span>
          <span>{benchmark.dataset_key ? benchmark.dataset_key.slice(0, 8) + "…" : "—"}</span>
        </div>

        {benchmark.notes && (
          <p className="text-xs text-muted-foreground border-t pt-2">{benchmark.notes}</p>
        )}

        {transitions.length > 0 && (
          <div className="border-t pt-3">
            <p className="text-xs font-medium mb-1.5">Lifecycle transition</p>
            <div className="flex gap-2">
              {transitions.map((s) => (
                <button
                  key={s}
                  onClick={() => handleTransition(s)}
                  disabled={transitioning}
                  className="rounded border px-3 py-1 text-xs hover:bg-muted disabled:opacity-50"
                >
                  → {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {error && <p className="text-xs text-red-600">{error}</p>}

        {benchmark.dataset_key && <DatasetPolicyPanel datasetKey={benchmark.dataset_key} />}
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// BenchmarksPage
// ---------------------------------------------------------------------------

export function BenchmarksPage() {
  const [benchmarks, setBenchmarks] = useState<Benchmark[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selected, setSelected] = useState<Benchmark | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([listBenchmarks(), listDatasets()]).then(([bs, ds]) => {
      setBenchmarks(bs);
      setDatasets(ds);
      setLoading(false);
    });
  }, []);

  function handleCreated(b: Benchmark) {
    setBenchmarks((prev) => [...prev, b]);
    setSelected(b);
  }

  function handleUpdated(updated: Benchmark) {
    setBenchmarks((prev) =>
      prev.map((b) => (b.entity_key === updated.entity_key ? updated : b)),
    );
    setSelected(updated);
  }

  if (loading) return <Spinner />;

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-semibold">Benchmarks</h1>
      <div className="grid grid-cols-3 gap-4">
        {/* Left: create form */}
        <div className="space-y-4">
          <BenchmarkCreateForm datasets={datasets} onCreated={handleCreated} />
        </div>

        {/* Middle: benchmark list */}
        <div className="space-y-2">
          <p className="text-xs font-medium text-muted-foreground uppercase">
            {benchmarks.length} benchmark{benchmarks.length !== 1 ? "s" : ""}
          </p>
          {benchmarks.map((b) => (
            <button
              key={b.entity_key}
              onClick={() => setSelected(b)}
              className={`w-full text-left rounded border p-3 text-sm transition-colors hover:bg-muted ${
                selected?.entity_key === b.entity_key ? "border-primary bg-muted" : ""
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium truncate">{b.name}</span>
                <Badge variant={STATUS_VARIANT[b.status] ?? "muted"}>{b.status}</Badge>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                {b.domain || "—"} · {b.task_type || "—"} · v{b.version}
              </p>
            </button>
          ))}
          {benchmarks.length === 0 && (
            <p className="text-xs text-muted-foreground">No benchmarks yet.</p>
          )}
        </div>

        {/* Right: detail panel */}
        <div>
          {selected ? (
            <BenchmarkDetail
              benchmark={selected}
              onUpdated={handleUpdated}
            />
          ) : (
            <p className="text-xs text-muted-foreground">Select a benchmark to view details.</p>
          )}
        </div>
      </div>
    </div>
  );
}
