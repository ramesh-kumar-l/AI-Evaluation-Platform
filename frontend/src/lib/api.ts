import type {
  Health,
  Evaluation,
  EvaluationResult,
  Metric,
  Dataset,
  AuditEvent,
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
