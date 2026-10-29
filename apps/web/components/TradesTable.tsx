"use client";

import type { Trade } from "@/lib/api";

const d = (s: string) => new Date(s).toLocaleDateString();

export default function TradesTable({ trades }: { trades: Trade[] }) {
  if (trades.length === 0) {
    return (
      <p className="rounded border border-border bg-surface p-4 text-sm text-muted">
        Sin round-trips cerrados (p. ej. buy &amp; hold no cierra posiciones).
      </p>
    );
  }
  return (
    <div className="overflow-auto rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="bg-surface-2 text-[11px] uppercase tracking-wide text-muted">
          <tr>
            <th className="px-3 py-2 text-left font-medium">Entrada</th>
            <th className="px-3 py-2 text-left font-medium">Salida</th>
            <th className="px-3 py-2 text-right font-medium">Precio in</th>
            <th className="px-3 py-2 text-right font-medium">Precio out</th>
            <th className="px-3 py-2 text-right font-medium">PnL</th>
            <th className="px-3 py-2 text-right font-medium">Retorno</th>
          </tr>
        </thead>
        <tbody className="nums">
          {trades.map((t, i) => (
            <tr key={i} className="border-t border-border hover:bg-surface-2/50">
              <td className="px-3 py-1.5 text-left text-muted">{d(t.entry_time)}</td>
              <td className="px-3 py-1.5 text-left text-muted">{d(t.exit_time)}</td>
              <td className="px-3 py-1.5 text-right">{t.entry_price.toFixed(2)}</td>
              <td className="px-3 py-1.5 text-right">{t.exit_price.toFixed(2)}</td>
              <td className={`px-3 py-1.5 text-right ${t.pnl >= 0 ? "text-pos" : "text-neg"}`}>
                {t.pnl >= 0 ? "+" : ""}
                {t.pnl.toFixed(2)}
              </td>
              <td
                className={`px-3 py-1.5 text-right ${t.return_pct >= 0 ? "text-pos" : "text-neg"}`}
              >
                {t.return_pct >= 0 ? "+" : ""}
                {(t.return_pct * 100).toFixed(2)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
