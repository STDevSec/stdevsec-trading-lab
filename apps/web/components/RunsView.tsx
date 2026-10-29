"use client";

import { useEffect, useState } from "react";
import { api, type Run } from "@/lib/api";

const pct = (x: number) => `${x >= 0 ? "+" : ""}${(x * 100).toFixed(2)}%`;
const dt = (s: string) => new Date(s).toLocaleString();

export default function RunsView({ onSelect }: { onSelect: (id: string) => void }) {
  const [runs, setRuns] = useState<Run[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listBacktests()
      .then((p) => setRuns(p.items))
      .catch((e) => setError(String(e)));
  }, []);

  if (error) {
    return (
      <p className="rounded border border-neg/40 bg-neg/10 p-3 text-sm text-neg">{error}</p>
    );
  }
  if (runs === null) return <p className="text-sm text-muted">Cargando corridas…</p>;
  if (runs.length === 0) {
    return (
      <p className="rounded-lg border border-border bg-surface p-6 text-sm text-muted">
        Aún no hay corridas. Lanza un backtest y aparecerá aquí.
      </p>
    );
  }

  return (
    <div className="overflow-auto rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="bg-surface-2 text-[11px] uppercase tracking-wide text-muted">
          <tr>
            <th className="px-4 py-2.5 text-left font-medium">Fecha</th>
            <th className="px-4 py-2.5 text-left font-medium">Estrategia</th>
            <th className="px-4 py-2.5 text-right font-medium">Retorno</th>
            <th className="px-4 py-2.5 text-right font-medium">Max DD</th>
            <th className="px-4 py-2.5 text-right font-medium">Sharpe</th>
            <th className="px-4 py-2.5 text-right font-medium">Trades</th>
            <th className="px-4 py-2.5 text-right font-medium">Equity final</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((r) => (
            <tr
              key={r.id}
              onClick={() => onSelect(r.id)}
              className="cursor-pointer border-t border-border hover:bg-surface-2/60"
            >
              <td className="px-4 py-2.5 text-left text-muted">{dt(r.created_at)}</td>
              <td className="px-4 py-2.5 text-left">{r.strategy_name}</td>
              <td
                className={`nums px-4 py-2.5 text-right ${r.total_return >= 0 ? "text-pos" : "text-neg"}`}
              >
                {pct(r.total_return)}
              </td>
              <td className="nums px-4 py-2.5 text-right text-muted">
                {(r.metrics.max_drawdown * 100).toFixed(2)}%
              </td>
              <td className="nums px-4 py-2.5 text-right">
                {r.metrics.sharpe === null ? "—" : r.metrics.sharpe.toFixed(2)}
              </td>
              <td className="nums px-4 py-2.5 text-right text-muted">{r.metrics.n_trades}</td>
              <td className="nums px-4 py-2.5 text-right">{r.final_equity.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
