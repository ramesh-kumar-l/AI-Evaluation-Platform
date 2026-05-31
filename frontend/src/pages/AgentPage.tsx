import { useEffect, useState } from "react";
import type { AgentEval, AgentEvalResult, AgentRun, Dataset } from "@/types";
import {
  getAgentEvalResults,
  listAgentRuns,
  listDatasets,
  runAgentEval,
} from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { RunCreateForm, RunStepsPanel } from "@/pages/AgentRunPanels";

// ---------------------------------------------------------------------------
// EvalPanel
// ---------------------------------------------------------------------------

interface EvalPanelProps {
  agentName: string;
  datasets: Dataset[];
}

function EvalPanel({ agentName, datasets }: EvalPanelProps) {
  const [datasetKey, setDatasetKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [evalResult, setEvalResult] = useState<AgentEval | null>(null);
  const [perQuery, setPerQuery] = useState<AgentEvalResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function handleRun(e: React.FormEvent) {
    e.preventDefault();
    if (!datasetKey) return;
    setLoading(true);
    setError(null);
    setPerQuery([]);
    try {
      const ev = await runAgentEval({ dataset_key: datasetKey, agent_name: agentName });
      setEvalResult(ev);
      setPerQuery(await getAgentEvalResults(ev.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evaluation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-3">
      <form onSubmit={handleRun} className="flex gap-2 items-end flex-wrap">
        <div className="flex-1 min-w-40">
          <label className="block text-xs text-muted-foreground mb-1">Query dataset</label>
          <select
            className="w-full border rounded px-2 py-1.5 text-sm"
            value={datasetKey}
            onChange={(e) => setDatasetKey(e.target.value)}
            required
          >
            <option value="">Select dataset…</option>
            {datasets.map((d) => (
              <option key={d.entity_key} value={d.entity_key}>
                {d.name}
              </option>
            ))}
          </select>
        </div>
        <button
          type="submit"
          disabled={loading || !datasetKey}
          className="bg-primary text-primary-foreground rounded px-3 py-1.5 text-sm disabled:opacity-50"
        >
          {loading ? <Spinner /> : "Run Evaluation"}
        </button>
      </form>
      {error && <p className="text-xs text-red-500">{error}</p>}
      {evalResult && (
        <div className="space-y-2">
          <div className="grid grid-cols-3 gap-2 text-xs">
            {[
              { label: "Tool Accuracy", value: evalResult.mean_tool_accuracy },
              { label: "Trajectory Score", value: evalResult.mean_trajectory_score },
              { label: "Task Completion", value: evalResult.mean_task_completion },
            ].map(({ label, value }) => (
              <div key={label} className="border rounded p-2 text-center">
                <div className="font-semibold text-base">{(value * 100).toFixed(1)}%</div>
                <div className="text-muted-foreground">{label}</div>
              </div>
            ))}
          </div>
          <p className="text-xs text-muted-foreground">
            {evalResult.query_count} queries · {evalResult.status}
          </p>
          {perQuery.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs font-semibold">Per-query breakdown</p>
              {perQuery.map((r, i) => (
                <div key={r.id} className="border rounded px-2 py-1.5 text-xs space-y-0.5">
                  <div className="font-medium">
                    Q{i + 1}: {r.query_text}
                  </div>
                  <div className="flex gap-3 text-muted-foreground">
                    <span>TA: {(r.tool_call_accuracy * 100).toFixed(1)}%</span>
                    <span>Traj: {(r.trajectory_score * 100).toFixed(1)}%</span>
                    <span>TC: {(r.task_completion_score * 100).toFixed(1)}%</span>
                  </div>
                  {r.expected_tools.length > 0 && (
                    <div className="text-muted-foreground">
                      Expected tools: {r.expected_tools.join(", ")} · Got:{" "}
                      {r.actual_tools.join(", ") || "none"}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// AgentDetail — runs list + evaluate tabs
// ---------------------------------------------------------------------------

interface AgentDetailProps {
  agentName: string;
  runs: AgentRun[];
  datasets: Dataset[];
  onRunAdded: (run: AgentRun) => void;
}

function AgentDetail({ agentName, runs, datasets, onRunAdded }: AgentDetailProps) {
  const [tab, setTab] = useState<"runs" | "eval">("runs");
  const tabs: Array<{ id: typeof tab; label: string }> = [
    { id: "runs", label: "Runs" },
    { id: "eval", label: "Evaluate" },
  ];

  return (
    <Card>
      <div className="space-y-3">
        <div>
          <h3 className="font-semibold text-sm">{agentName}</h3>
          <p className="text-xs text-muted-foreground">{runs.length} runs recorded</p>
        </div>
        <div className="flex gap-1 border-b pb-2">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-3 py-1 text-xs rounded ${
                tab === t.id
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        {tab === "runs" && (
          <div className="space-y-2">
            <RunCreateForm onCreated={onRunAdded} />
            {runs.length > 0 && (
              <div className="space-y-1">
                {runs.map((r) => (
                  <RunStepsPanel key={r.id} run={r} />
                ))}
              </div>
            )}
            {runs.length === 0 && (
              <p className="text-xs text-muted-foreground">
                No runs yet. Submit a run above.
              </p>
            )}
          </div>
        )}
        {tab === "eval" && <EvalPanel agentName={agentName} datasets={datasets} />}
      </div>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// AgentPage
// ---------------------------------------------------------------------------

export function AgentPage() {
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([listAgentRuns(), listDatasets()])
      .then(([r, d]) => {
        setRuns(r);
        setDatasets(d);
        if (r.length > 0) setSelectedAgent(r[0].agent_name);
      })
      .finally(() => setLoading(false));
  }, []);

  const agentNames = [...new Set(runs.map((r) => r.agent_name))];
  const selectedRuns = runs.filter((r) => r.agent_name === selectedAgent);

  function handleRunAdded(run: AgentRun) {
    setRuns((prev) => [run, ...prev]);
    setSelectedAgent(run.agent_name);
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-lg font-semibold">Agent & Tool Evaluation</h1>
        <p className="text-xs text-muted-foreground">
          Submit agent trajectories, inspect tool calls, and score grounding quality.
        </p>
      </div>
      <div className="grid grid-cols-[220px_1fr] gap-4">
        <div className="space-y-3">
          {agentNames.length > 0 && (
            <Card>
              <h2 className="text-xs font-semibold text-muted-foreground mb-2">AGENTS</h2>
              <ul className="space-y-0.5">
                {agentNames.map((name) => (
                  <li key={name}>
                    <button
                      onClick={() => setSelectedAgent(name)}
                      className={`w-full text-left px-2 py-1.5 rounded text-sm truncate ${
                        selectedAgent === name
                          ? "bg-primary text-primary-foreground"
                          : "hover:bg-muted"
                      }`}
                    >
                      {name}
                    </button>
                  </li>
                ))}
              </ul>
            </Card>
          )}
          {agentNames.length === 0 && (
            <p className="text-xs text-muted-foreground px-1">
              Submit a run to register an agent.
            </p>
          )}
        </div>
        <div>
          {selectedAgent ? (
            <AgentDetail
              agentName={selectedAgent}
              runs={selectedRuns}
              datasets={datasets}
              onRunAdded={handleRunAdded}
            />
          ) : (
            <Card>
              <RunCreateForm onCreated={handleRunAdded} />
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
