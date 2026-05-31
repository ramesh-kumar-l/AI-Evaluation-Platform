// Minimal API client. Base URL is build-time configurable; defaults to the local backend.
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export interface Health {
  status: string;
  service: string;
  version: string;
  env: string;
  offline_first: boolean;
}

export async function getHealth(): Promise<Health> {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return (await res.json()) as Health;
}
