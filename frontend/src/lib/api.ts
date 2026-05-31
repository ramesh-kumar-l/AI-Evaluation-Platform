import type {
  Approval,
  AuditEvent,
  Benchmark,
  Comparison,
  Dataset,
  DatasetPolicy,
  Evaluation,
  EvaluationResult,
  GateDecision,
  Health,
  Metric,
  ReleaseGate,
} from "@/types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, init);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export function getHealth(): Promise<Health> {
  return request<Health>("/health");
}

export function listEvaluations(params?: {
  dataset_key?: string;
  model_key?: string;
}): Promise<Evaluation[]> {
  const q = new URLSearchParams();
  if (params?.dataset_key) q.set("dataset_key", params.dataset_key);
  if (params?.model_key) q.set("model_key", params.model_key);
  const qs = q.toString();
  return request<Evaluation[]>(`/evaluations${qs ? `?${qs}` : ""}`);
}

export function getEvaluation(id: string): Promise<Evaluation> {
  return request<Evaluation>(`/evaluations/${id}`);
}

export function getEvaluationResults(
  id: string,
  metricKey?: string,
): Promise<EvaluationResult[]> {
  const qs = metricKey ? `?metric_key=${metricKey}` : "";
  return request<EvaluationResult[]>(`/evaluations/${id}/results${qs}`);
}

export function listMetrics(): Promise<Metric[]> {
  return request<Metric[]>("/metrics");
}

export function getMetric(key: string): Promise<Metric> {
  return request<Metric>(`/metrics/${key}`);
}

export function listDatasets(): Promise<Dataset[]> {
  return request<Dataset[]>("/datasets");
}

export function listAuditEvents(params?: {
  entity_key?: string;
  limit?: number;
}): Promise<AuditEvent[]> {
  const q = new URLSearchParams();
  if (params?.entity_key) q.set("entity_key", params.entity_key);
  if (params?.limit) q.set("limit", String(params.limit));
  const qs = q.toString();
  return request<AuditEvent[]>(`/audit/events${qs ? `?${qs}` : ""}`);
}

export function createComparison(body: {
  name: string;
  baseline_id: string;
  candidate_id: string;
  kind?: string;
  threshold_config?: Record<string, number>;
  notes?: string;
}): Promise<Comparison> {
  return request<Comparison>("/comparisons", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function listComparisons(params?: {
  baseline_id?: string;
  candidate_id?: string;
  dataset_key?: string;
  status?: string;
}): Promise<Comparison[]> {
  const q = new URLSearchParams();
  if (params?.baseline_id) q.set("baseline_id", params.baseline_id);
  if (params?.candidate_id) q.set("candidate_id", params.candidate_id);
  if (params?.dataset_key) q.set("dataset_key", params.dataset_key);
  if (params?.status) q.set("status", params.status);
  const qs = q.toString();
  return request<Comparison[]>(`/comparisons${qs ? `?${qs}` : ""}`);
}

export function getComparison(id: string): Promise<Comparison> {
  return request<Comparison>(`/comparisons/${id}`);
}

// ---------------------------------------------------------------------------
// Release Gates
// ---------------------------------------------------------------------------

export function createGate(body: {
  name: string;
  description?: string;
  criteria: { metric_key: string; min_score: number }[];
  max_regressions_allowed?: number;
  require_approval?: boolean;
  notes?: string;
}): Promise<ReleaseGate> {
  return request<ReleaseGate>("/gates", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function listGates(): Promise<ReleaseGate[]> {
  return request<ReleaseGate[]>("/gates");
}

export function getGate(gateKey: string): Promise<ReleaseGate> {
  return request<ReleaseGate>(`/gates/${gateKey}`);
}

export function evaluateGate(
  gateKey: string,
  comparisonId: string,
): Promise<GateDecision> {
  return request<GateDecision>(`/gates/${gateKey}/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ comparison_id: comparisonId }),
  });
}

export function listGateDecisions(gateKey: string): Promise<GateDecision[]> {
  return request<GateDecision[]>(`/gates/${gateKey}/decisions`);
}

export function approveDecision(
  decisionId: string,
  body: { action: string; justification: string },
): Promise<Approval> {
  return request<Approval>(`/gates/decisions/${decisionId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

// ---------------------------------------------------------------------------
// Phase 7 — Benchmarks
// ---------------------------------------------------------------------------

export function createBenchmark(body: {
  name: string;
  description?: string;
  domain?: string;
  task_type?: string;
  metric_keys?: string[];
  dataset_key?: string | null;
  notes?: string | null;
}): Promise<Benchmark> {
  return request<Benchmark>("/benchmarks", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function listBenchmarks(byStatus?: string): Promise<Benchmark[]> {
  const qs = byStatus ? `?by_status=${byStatus}` : "";
  return request<Benchmark[]>(`/benchmarks${qs}`);
}

export function getBenchmark(benchmarkKey: string): Promise<Benchmark> {
  return request<Benchmark>(`/benchmarks/${benchmarkKey}`);
}

export function setBenchmarkStatus(
  benchmarkKey: string,
  body: { status: string; notes?: string | null },
): Promise<Benchmark> {
  return request<Benchmark>(`/benchmarks/${benchmarkKey}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

// ---------------------------------------------------------------------------
// Phase 7 — Dataset Policies
// ---------------------------------------------------------------------------

export function upsertDatasetPolicy(
  datasetKey: string,
  body: {
    owner?: string;
    status?: string;
    quality_rules?: Record<string, unknown>;
    ground_truth_policy?: Record<string, unknown>;
    notes?: string | null;
  },
): Promise<DatasetPolicy> {
  return request<DatasetPolicy>(`/datasets/${datasetKey}/policy`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function getDatasetPolicy(datasetKey: string): Promise<DatasetPolicy> {
  return request<DatasetPolicy>(`/datasets/${datasetKey}/policy`);
}
