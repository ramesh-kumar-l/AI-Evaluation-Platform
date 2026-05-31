import { useEffect, useState } from "react";
import { getHealth, type Health } from "@/lib/api";

// Phase 0 shell: proves the frontend boots, reaches the API, and renders the trust-first theme.
// The full navigation shell and trust components arrive in Phase 4.
export function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch((e) => setError(String(e)));
  }, []);

  return (
    <main className="min-h-screen flex items-center justify-center p-8">
      <div className="w-full max-w-md rounded-lg border bg-card text-card-foreground shadow-sm p-6">
        <h1 className="text-xl font-semibold">AI Evaluation Platform</h1>
        <p className="text-sm text-muted-foreground mt-1">
          System of record for AI quality. <em>Can we safely deploy?</em>
        </p>

        <div className="mt-6 flex items-center gap-2">
          <span
            className={`inline-block h-2.5 w-2.5 rounded-full ${
              health ? "bg-trust" : error ? "bg-danger" : "bg-warning"
            }`}
          />
          <span className="text-sm">
            {health ? `API ${health.status} · v${health.version}` : error ? "API unreachable" : "Checking…"}
          </span>
        </div>

        {health && (
          <p className="mt-2 text-xs text-muted-foreground">
            env: {health.env} · offline-first: {String(health.offline_first)}
          </p>
        )}
      </div>
    </main>
  );
}
