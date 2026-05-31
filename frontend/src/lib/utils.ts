export function shortId(id: string): string {
  return id.slice(0, 8);
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

export function formatScore(score: number): string {
  return `${(score * 100).toFixed(1)}%`;
}

export function scoreColor(score: number): string {
  if (score >= 0.8) return "text-trust";
  if (score >= 0.5) return "text-warning";
  return "text-danger";
}

export function confidenceVariant(confidence: string): "trust" | "warning" | "muted" {
  if (confidence === "high") return "trust";
  if (confidence === "medium") return "warning";
  return "muted";
}

export function statusVariant(status: string): "trust" | "warning" | "danger" {
  if (status === "completed") return "trust";
  if (status === "partial") return "warning";
  return "danger";
}
