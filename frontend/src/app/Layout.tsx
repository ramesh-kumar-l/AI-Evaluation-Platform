import { NavLink, Outlet } from "react-router-dom";

const NAV_ITEMS: Array<{ to: string; label: string; end?: boolean }> = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/evaluations", label: "Evaluations" },
  { to: "/compare", label: "Compare" },
  { to: "/gates", label: "Release Gates" },
  { to: "/benchmarks", label: "Benchmarks" },
  { to: "/rag", label: "RAG Eval" },
  { to: "/agent", label: "Agent Eval" },
  { to: "/datasets", label: "Datasets" },
  { to: "/audit", label: "Audit Trail" },
];

export function Layout() {
  return (
    <div className="flex min-h-screen">
      <aside className="w-52 shrink-0 border-r bg-card flex flex-col">
        <div className="px-4 py-5 border-b">
          <h1 className="text-sm font-semibold leading-tight">
            AI Evaluation
            <br />
            Platform
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">System of record</p>
        </div>

        <nav className="flex-1 p-2" aria-label="Main navigation">
          <ul className="space-y-0.5">
            {NAV_ITEMS.map(({ to, label, end }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  end={end}
                  className={({ isActive }) =>
                    `block rounded-md px-3 py-2 text-sm transition-colors ${
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "text-foreground hover:bg-muted"
                    }`
                  }
                >
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className="px-4 py-3 border-t">
          <p className="text-xs text-muted-foreground">Offline-first · v0.1</p>
        </div>
      </aside>

      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
