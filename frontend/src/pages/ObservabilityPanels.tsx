import { useState, useEffect } from "react";
import type { EvalSchedule, EvalJob } from "@/types";
import {
  createEvalSchedule,
  listEvalSchedules,
  updateScheduleStatus,
  triggerSchedule,
  listEvalJobs,
} from "@/lib/api";

// ---------------------------------------------------------------------------
// ScheduleCreateForm
// ---------------------------------------------------------------------------

interface ScheduleFormProps {
  onCreated: (s: EvalSchedule) => void;
}

export function ScheduleCreateForm({ onCreated }: ScheduleFormProps) {
  const [name, setName] = useState("");
  const [datasetKey, setDatasetKey] = useState("");
  const [modelKey, setModelKey] = useState("");
  const [promptKey, setPromptKey] = useState("");
  const [metricKeys, setMetricKeys] = useState("");
  const [cronExpr, setCronExpr] = useState("0 * * * *");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const s = await createEvalSchedule({
        name,
        dataset_key: datasetKey,
        model_key: modelKey,
        prompt_key: promptKey,
        metric_keys: metricKeys.split(",").map((k) => k.trim()).filter(Boolean),
        cron_expr: cronExpr,
      });
      setName(""); setDatasetKey(""); setModelKey("");
      setPromptKey(""); setMetricKeys(""); setCronExpr("0 * * * *");
      onCreated(s);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create schedule");
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <h3 className="font-medium text-sm">New Schedule</h3>
      {error && <p className="text-destructive text-xs">{error}</p>}
      <input className="w-full border rounded px-2 py-1 text-sm" placeholder="Name"
        value={name} onChange={(e) => setName(e.target.value)} required />
      <input className="w-full border rounded px-2 py-1 text-sm font-mono text-xs"
        placeholder="Dataset key (UUID)" value={datasetKey}
        onChange={(e) => setDatasetKey(e.target.value)} required />
      <input className="w-full border rounded px-2 py-1 text-sm font-mono text-xs"
        placeholder="Model key (UUID)" value={modelKey}
        onChange={(e) => setModelKey(e.target.value)} required />
      <input className="w-full border rounded px-2 py-1 text-sm font-mono text-xs"
        placeholder="Prompt key (UUID)" value={promptKey}
        onChange={(e) => setPromptKey(e.target.value)} required />
      <input className="w-full border rounded px-2 py-1 text-sm font-mono text-xs"
        placeholder="Metric keys (comma-separated UUIDs)" value={metricKeys}
        onChange={(e) => setMetricKeys(e.target.value)} />
      <input className="w-full border rounded px-2 py-1 text-sm font-mono"
        placeholder="Cron (e.g. 0 * * * *)" value={cronExpr}
        onChange={(e) => setCronExpr(e.target.value)} required />
      <button type="submit" disabled={loading}
        className="bg-primary text-primary-foreground px-3 py-1.5 rounded text-sm">
        {loading ? "Creating…" : "Create Schedule"}
      </button>
    </form>
  );
}

// ---------------------------------------------------------------------------
// ScheduleList
// ---------------------------------------------------------------------------

interface ScheduleListProps {
  schedules: EvalSchedule[];
  onRefresh: () => void;
}

export function ScheduleList({ schedules, onRefresh }: ScheduleListProps) {
  const [jobs, setJobs] = useState<Record<string, EvalJob[]>>({});
  const [triggering, setTriggering] = useState<string | null>(null);

  async function handleTrigger(scheduleKey: string) {
    setTriggering(scheduleKey);
    try {
      const job = await triggerSchedule(scheduleKey);
      setJobs((prev) => ({
        ...prev,
        [scheduleKey]: [job, ...(prev[scheduleKey] ?? [])],
      }));
    } finally {
      setTriggering(null);
    }
  }

  async function handleStatus(scheduleKey: string, status: string) {
    await updateScheduleStatus(scheduleKey, status);
    onRefresh();
  }

  async function loadJobs(scheduleKey: string) {
    const j = await listEvalJobs(scheduleKey);
    setJobs((prev) => ({ ...prev, [scheduleKey]: j }));
  }

  if (schedules.length === 0) {
    return <p className="text-sm text-muted-foreground">No schedules yet.</p>;
  }

  return (
    <div className="space-y-3">
      {schedules.map((s) => (
        <div key={s.entity_key} className="border rounded p-3 text-sm">
          <div className="flex items-center justify-between">
            <span className="font-medium">{s.name}</span>
            <span className={`text-xs px-1.5 py-0.5 rounded ${
              s.status === "active" ? "bg-green-100 text-green-800"
              : s.status === "paused" ? "bg-yellow-100 text-yellow-800"
              : "bg-gray-100 text-gray-600"}`}>
              {s.status}
            </span>
          </div>
          <p className="text-xs text-muted-foreground font-mono mt-1">{s.cron_expr}</p>
          <div className="flex gap-2 mt-2 flex-wrap">
            {s.status === "active" && (
              <button onClick={() => handleTrigger(s.entity_key)}
                disabled={triggering === s.entity_key}
                className="text-xs border rounded px-2 py-1">
                {triggering === s.entity_key ? "Running…" : "Trigger now"}
              </button>
            )}
            {s.status === "active" && (
              <button onClick={() => handleStatus(s.entity_key, "paused")}
                className="text-xs border rounded px-2 py-1">Pause</button>
            )}
            {s.status === "paused" && (
              <>
                <button onClick={() => handleStatus(s.entity_key, "active")}
                  className="text-xs border rounded px-2 py-1">Resume</button>
                <button onClick={() => handleStatus(s.entity_key, "archived")}
                  className="text-xs border rounded px-2 py-1 text-destructive">Archive</button>
              </>
            )}
            <button onClick={() => loadJobs(s.entity_key)}
              className="text-xs text-primary underline">History</button>
          </div>
          {jobs[s.entity_key] && (
            <ul className="mt-2 space-y-1">
              {jobs[s.entity_key].map((j) => (
                <li key={j.id} className="text-xs font-mono flex gap-2">
                  <span className={j.status === "completed" ? "text-green-700"
                    : j.status === "failed" ? "text-destructive" : "text-muted-foreground"}>
                    {j.status}
                  </span>
                  <span className="text-muted-foreground">
                    {new Date(j.started_at).toLocaleString()}
                  </span>
                  {j.error_msg && <span className="text-destructive">{j.error_msg}</span>}
                </li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// SchedulePanel (combines form + list)
// ---------------------------------------------------------------------------

export function SchedulePanel() {
  const [schedules, setSchedules] = useState<EvalSchedule[]>([]);

  async function load() {
    const s = await listEvalSchedules();
    setSchedules(s);
  }

  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-6">
      <ScheduleCreateForm onCreated={(s) => setSchedules((prev) => [s, ...prev])} />
      <div>
        <h3 className="font-medium text-sm mb-2">Schedules</h3>
        <ScheduleList schedules={schedules} onRefresh={load} />
      </div>
    </div>
  );
}
