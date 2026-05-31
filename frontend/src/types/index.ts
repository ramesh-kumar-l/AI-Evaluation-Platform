export interface Health {
  status: string;
  service: string;
  version: string;
  env: string;
  offline_first: boolean;
}

export interface VersionedEntity {
  id: string;
  entity_key: string;
  version: number;
  is_latest: boolean;
  created_at: string;
  created_by: string;
  parent_version_id: string | null;
}

export interface Prompt extends VersionedEntity {
  name: string;
  description: string;
  template: string;
  input_variables: string[];
}

export interface DatasetItem {
  input: Record<string, unknown>;
  expected: string;
}

export interface Dataset extends VersionedEntity {
  name: string;
  description: string;
  items: DatasetItem[];
  item_count: number;
}

export interface Metric extends VersionedEntity {
  name: string;
  description: string;
  kind: "exact_match" | "contains" | "semantic_similarity";
  config: Record<string, unknown>;
}

export interface ConfidenceDistribution {
  high?: number;
  medium?: number;
  low?: number;
}

export interface AggregateScore {
  mean_score: number;
  count: number;
  metric_name: string;
  metric_kind: string;
  confidence_distribution: ConfidenceDistribution;
}

export interface Evaluation {
  id: string;
  name: string;
  prompt_key: string;
  prompt_version_id: string;
  model_key: string;
  model_version_id: string;
  provider_key: string;
  dataset_key: string;
  dataset_version_id: string;
  metric_keys: string[];
  metric_version_ids: string[];
  parameters: Record<string, unknown>;
  status: "completed" | "partial" | "failed";
  total_items: number;
  scored_items: number;
  aggregate_scores: Record<string, AggregateScore>;
  error: string | null;
  created_at: string;
  created_by: string;
}

export interface EvaluationResult {
  id: string;
  evaluation_id: string;
  run_id: string;
  dataset_item_index: number;
  metric_key: string;
  metric_kind: string;
  score: number;
  confidence: string;
  detail: Record<string, unknown>;
  status: string;
  created_at: string;
}

export interface AuditEvent {
  seq: number;
  id: string;
  occurred_at: string;
  actor: string;
  action: string;
  entity_type: string;
  entity_key: string;
  entity_version_id: string | null;
  payload: Record<string, unknown>;
  prev_hash: string | null;
  hash: string;
}

export interface MetricDelta {
  metric_name: string;
  metric_kind: string;
  baseline_score: number;
  candidate_score: number;
  delta: number;
  relative_delta: number;
  regression: boolean;
  improvement: boolean;
  threshold: number;
}

export interface Comparison {
  id: string;
  name: string;
  created_at: string;
  created_by: string;
  baseline_id: string;
  candidate_id: string;
  kind: string;
  dataset_key: string;
  metric_deltas: Record<string, MetricDelta>;
  threshold_config: Record<string, number>;
  regressions_detected: number;
  improvements_detected: number;
  status: "regression" | "improvement" | "neutral";
  notes: string | null;
}

export interface GateCriterion {
  metric_key: string;
  min_score: number;
}

export interface ReleaseGate {
  id: string;
  entity_key: string;
  version: number;
  parent_id: string | null;
  is_latest: boolean;
  created_at: string;
  created_by: string;
  name: string;
  description: string;
  criteria: GateCriterion[];
  max_regressions_allowed: number;
  require_approval: boolean;
  notes: string | null;
}

export interface CriterionResult {
  metric_key: string;
  min_score: number;
  candidate_score: number;
  passed: boolean;
}

export type GateDecisionStatus =
  | "passed"
  | "failed"
  | "pending_approval"
  | "approved"
  | "rejected"
  | "overridden";

export interface GateDecision {
  id: string;
  gate_key: string;
  gate_version_id: string;
  comparison_id: string;
  criteria_results: Record<string, CriterionResult>;
  criteria_passed: number;
  criteria_failed: number;
  regressions_detected: number;
  max_regressions_allowed: number;
  status: GateDecisionStatus;
  override: boolean;
  override_justification: string | null;
  created_at: string;
  created_by: string;
}

export interface Approval {
  id: string;
  decision_id: string;
  action: "approved" | "rejected" | "overridden";
  justification: string;
  created_at: string;
  created_by: string;
}

// ---------------------------------------------------------------------------
// Phase 7 — Dataset & Benchmark Governance
// ---------------------------------------------------------------------------

export type BenchmarkStatus = "draft" | "active" | "deprecated" | "archived";

export interface Benchmark {
  id: string;
  entity_key: string;
  version: number;
  parent_id: string | null;
  is_latest: boolean;
  created_at: string;
  created_by: string;
  name: string;
  description: string;
  domain: string;
  task_type: string;
  metric_keys: string[];
  dataset_key: string | null;
  status: BenchmarkStatus;
  notes: string | null;
}

export interface DatasetPolicy {
  id: string;
  dataset_key: string;
  owner: string;
  status: "active" | "deprecated" | "archived";
  quality_rules: Record<string, unknown>;
  ground_truth_policy: Record<string, unknown>;
  notes: string | null;
  created_at: string;
  updated_at: string;
  created_by: string;
}

// ---------------------------------------------------------------------------
// Phase 8 — RAG Evaluation
// ---------------------------------------------------------------------------

export interface RagCorpus {
  id: string;
  entity_key: string;
  version: number;
  parent_id: string | null;
  is_latest: boolean;
  created_at: string;
  created_by: string;
  name: string;
  description: string;
  embedding_model: string;
  chunk_size: number;
  chunk_overlap: number;
}

export interface RagDocument {
  id: string;
  corpus_key: string;
  content: string;
  chunk_index: number;
  doc_source: string;
  created_at: string;
  created_by: string;
}

export interface RagSearchResult {
  doc_id: string;
  content: string;
  doc_source: string;
  score: number;
}

export interface RagSearchResponse {
  query: string;
  corpus_key: string;
  results: RagSearchResult[];
}

export interface RagEval {
  id: string;
  corpus_key: string;
  dataset_key: string;
  retrieval_method: string;
  top_k: number;
  query_count: number;
  mean_context_relevance: number;
  mean_faithfulness: number;
  mean_answer_relevance: number;
  status: string;
  created_at: string;
  created_by: string;
}

export interface RagEvalResult {
  id: string;
  rag_eval_id: string;
  query_text: string;
  retrieved_doc_ids: string[];
  retrieved_content: string[];
  answer_text: string;
  context_relevance_score: number;
  faithfulness_score: number;
  answer_relevance_score: number;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Phase 9 — Agent & Tool Evaluation
// ---------------------------------------------------------------------------

export interface AgentStep {
  id: string;
  agent_run_id: string;
  step_index: number;
  step_type: string;
  tool_name: string;
  tool_input: Record<string, unknown>;
  tool_output: string;
  reasoning_text: string;
  created_at: string;
}

export interface AgentRun {
  id: string;
  agent_name: string;
  query: string;
  final_answer: string;
  tool_calls: Array<Record<string, unknown>>;
  step_count: number;
  status: string;
  created_at: string;
  created_by: string;
}

export interface AgentEval {
  id: string;
  dataset_key: string;
  agent_name: string;
  query_count: number;
  mean_tool_accuracy: number;
  mean_trajectory_score: number;
  mean_task_completion: number;
  status: string;
  created_at: string;
  created_by: string;
}

export interface AgentEvalResult {
  id: string;
  agent_eval_id: string;
  query_text: string;
  expected_answer: string;
  actual_answer: string;
  expected_tools: string[];
  actual_tools: string[];
  tool_call_accuracy: number;
  trajectory_score: number;
  task_completion_score: number;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Phase 10 — Observability & Continuous Evaluation
// ---------------------------------------------------------------------------

export type ScheduleStatus = "active" | "paused" | "archived";
export type ExperimentStatus = "active" | "concluded" | "archived";

export interface EvalSchedule {
  id: string;
  entity_key: string;
  version: number;
  name: string;
  description: string;
  dataset_key: string;
  model_key: string;
  prompt_key: string;
  metric_keys: string[];
  cron_expr: string;
  status: ScheduleStatus;
  last_run_at: string | null;
  next_run_at: string | null;
  created_at: string;
  created_by: string;
}

export interface EvalJob {
  id: string;
  schedule_id: string;
  status: "pending" | "running" | "completed" | "failed";
  eval_id: string | null;
  error_msg: string;
  triggered_by: string;
  started_at: string;
  completed_at: string | null;
}

export interface Experiment {
  id: string;
  entity_key: string;
  version: number;
  name: string;
  description: string;
  evaluation_ids: string[];
  status: ExperimentStatus;
  hypothesis: string;
  conclusion: string;
  created_at: string;
  created_by: string;
}

export interface TrendPoint {
  eval_id: string;
  created_at: string;
  mean_score: number;
  status: string;
}

export interface TrendOut {
  dataset_key: string;
  metric_kind: string;
  points: TrendPoint[];
}
