import { useState } from "react";
import type { AgentRun, AgentStep } from "@/types";
import { getAgentRunSteps, submitAgentRun } from "@/lib/api";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";

// ---------------------------------------------------------------------------
// RunCreateForm
// ---------------------------------------------------------------------------

interface RunCreateFormProps {
  onCreated: (run: AgentRun) => void;
}

export function RunCreateForm({ onCreated }: RunCreateFormProps) {
  const [agentName, setAgentName] = useState("");
  const [query, setQuery] = useState("");
  const [finalAnswer, setFinalAnswer] = useState("");
  const [toolCallsRaw, setToolCallsRaw] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    let toolCalls: Array<Record<string, unknown>> = [];
    try {
      if (toolCallsRaw.trim()) {
        toolCalls = JSON.parse(toolCallsRaw) as Array<Record<string, unknown>>;
      }
      const run = await submitAgentRun({
        agent_name: agentName,
        query,
        final_answer: finalAnswer,
        tool_calls: toolCalls,
      });
      onCreated(run);
      setQuery("");
      setFinalAnswer("");
      setToolCallsRaw("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submit failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <h2 className="text-xs font-semibold text-muted-foreground mb-3">SUBMIT RUN</h2>
      <form onSubmit={handleSubmit} className="space-y-2">
        <input
          className="w-full border rounded px-2 py-1.5 text-sm"
          placeholder="Agent name (e.g. research-agent-v1)"
          value={agentName}
          onChange={(e) => setAgentName(e.target.value)}
          required
        />
        <input
          className="w-full border rounded px-2 py-1.5 text-sm"
          placeholder="Query / task"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          required
        />
        <input
          className="w-full border rounded px-2 py-1.5 text-sm"
          placeholder="Final answer"
          value={finalAnswer}
          onChange={(e) => setFinalAnswer(e.target.value)}
        />
        <textarea
          className="w-full border rounded px-2 py-1.5 text-sm font-mono text-xs"
          rows={3}
          placeholder={'Tool calls JSON, e.g. [{"name":"search","input":"q","output":"r"}]'}
          value={toolCallsRaw}
          onChange={(e) => setToolCallsRaw(e.target.value)}
        />
        {error && <p className="text-xs text-red-500">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-primary text-primary-foreground rounded py-1.5 text-sm disabled:opacity-50"
        >
          {loading ? <Spinner /> : "Submit Run"}
        </button>
      </form>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// RunStepsPanel
// ---------------------------------------------------------------------------

interface RunStepsPanelProps {
  run: AgentRun;
}

export function RunStepsPanel({ run }: RunStepsPanelProps) {
  const [steps, setSteps] = useState<AgentStep[] | null>(null);
  const [loading, setLoading] = useState(false);

  async function loadSteps() {
    setLoading(true);
    try {
      setSteps(await getAgentRunSteps(run.id));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <p className="text-xs font-medium truncate flex-1">{run.query}</p>
        <Badge variant={run.status === "completed" ? "trust" : "warning"} className="text-xs">
          {run.status}
        </Badge>
        <span className="text-xs text-muted-foreground">{run.step_count} steps</span>
        {steps === null && (
          <button
            onClick={loadSteps}
            disabled={loading}
            className="text-xs text-primary underline"
          >
            {loading ? "..." : "view steps"}
          </button>
        )}
      </div>
      {steps && steps.length > 0 && (
        <div className="space-y-1">
          {steps.map((s) => (
            <div key={s.id} className="border rounded px-2 py-1 text-xs bg-muted/30">
              <span className="font-mono text-muted-foreground mr-2">{s.step_index}.</span>
              <Badge variant="muted" className="text-xs mr-1">
                {s.step_type}
              </Badge>
              {s.tool_name && <span className="font-medium">{s.tool_name}</span>}
              {s.reasoning_text && (
                <span className="text-muted-foreground ml-1 italic">{s.reasoning_text}</span>
              )}
            </div>
          ))}
        </div>
      )}
      {steps && steps.length === 0 && (
        <p className="text-xs text-muted-foreground">No steps recorded.</p>
      )}
    </div>
  );
}
