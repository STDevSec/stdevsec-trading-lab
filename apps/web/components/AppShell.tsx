"use client";

import type { ReactNode } from "react";

export type ViewId = "backtest" | "runs" | "journal";

type NavItem = { id: ViewId; label: string; icon: ReactNode };
type SoonItem = { label: string; icon: ReactNode };

// Minimal inline icons (no icon dependency).
const I = {
  flask: (
    <path d="M9 3h6M10 3v5L5 18a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-10V3" />
  ),
  list: <path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />,
  book: <path d="M4 5a2 2 0 0 1 2-2h14v16H6a2 2 0 0 0-2 2V5zM20 19H6" />,
  activity: <path d="M3 12h4l3 8 4-16 3 8h4" />,
};

const icon = (path: ReactNode) => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.8"
    strokeLinecap="round"
    strokeLinejoin="round"
    className="h-4 w-4 shrink-0"
  >
    {path}
  </svg>
);

const NAV: NavItem[] = [
  { id: "backtest", label: "Backtest", icon: icon(I.flask) },
  { id: "runs", label: "Corridas", icon: icon(I.list) },
  { id: "journal", label: "Diario", icon: icon(I.book) },
];
const SOON: SoonItem[] = [{ label: "Paper trading", icon: icon(I.activity) }];

const TITLES: Record<ViewId, string> = {
  backtest: "Nuevo backtest",
  runs: "Corridas",
  journal: "Diario de trading",
};

export default function AppShell({
  active,
  onNavigate,
  children,
}: {
  active: ViewId;
  onNavigate: (v: ViewId) => void;
  children: ReactNode;
}) {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar (fixed; only the main area scrolls) */}
      <aside className="flex w-56 shrink-0 flex-col border-r border-border bg-surface">
        <div className="flex items-center gap-2 border-b border-border px-4 py-4">
          <span className="grid h-7 w-7 place-items-center rounded bg-accent/15 text-accent">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4">
              <path d="M3 17l5-6 4 4 5-8" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </span>
          <div className="leading-tight">
            <div className="text-sm font-semibold">Trading Lab</div>
            <div className="text-[10px] uppercase tracking-wide text-muted">STDevsec</div>
          </div>
        </div>

        <nav className="flex-1 space-y-1 p-2">
          {NAV.map((item) => {
            const on = active === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`flex w-full items-center gap-2.5 rounded px-3 py-2 text-sm transition ${
                  on
                    ? "bg-surface-2 font-medium text-fg shadow-[inset_2px_0_0_0] shadow-accent"
                    : "text-muted hover:bg-surface-2 hover:text-fg"
                }`}
              >
                {item.icon}
                {item.label}
              </button>
            );
          })}

          <div className="px-3 pb-1 pt-4 text-[10px] uppercase tracking-wide text-muted/70">
            Próximamente
          </div>
          {SOON.map((item) => (
            <div
              key={item.label}
              className="flex w-full cursor-not-allowed items-center gap-2.5 rounded px-3 py-2 text-sm text-muted/50"
            >
              {item.icon}
              {item.label}
              <span className="ml-auto rounded bg-surface-2 px-1.5 py-0.5 text-[9px] uppercase text-muted">
                pronto
              </span>
            </div>
          ))}
        </nav>

        <div className="border-t border-border p-3 text-[10px] leading-snug text-muted">
          Solo simulación. No es asesoría financiera ni desempeño real de mercado.
        </div>
      </aside>

      {/* Main */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-border px-6">
          <h1 className="text-sm font-semibold">{TITLES[active]}</h1>
          <span className="flex items-center gap-1.5 rounded-full border border-border bg-surface px-2.5 py-1 text-[11px] text-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-pos" />
            Simulación
          </span>
        </header>
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  );
}
