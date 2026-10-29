"use client";

import { useEffect, useState } from "react";
import {
  api,
  candlesToCsv,
  syntheticCandles,
  type Dataset,
  type EquityPoint,
  type Metrics,
  type Run,
  type Strategy,
  type Trade,
} from "@/lib/api";
import AppShell, { type ViewId } from "@/components/AppShell";
import EquityChart from "@/components/EquityChart";
import RunsView from "@/components/RunsView";
import TradesTable from "@/components/TradesTable";

const pct = (x: number) => `${x >= 0 ? "+" : ""}${(x * 100).toFixed(2)}%`;
const num = (x: number | null, d = 2) => (x === null ? "—" : x.toFixed(d));

const INPUT =
  "rounded border border-border bg-surface-2 px-2 py-1.5 text-sm text-fg placeholder:text-muted focus:border-accent focus:outline-none";

export default function TradingLab() {
  const [view, setView] = useState<ViewId>("backtest");

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [datasetId, setDatasetId] = useState("");
  const [strategyName, setStrategyName] = useState("");
  const [params, setParams] = useState<Record<string, number>>({});
  const [capital, setCapital] = useState(10000);
  const [commissionBps, setCommissionBps] = useState(0);
  const [symbol, setSymbol] = useState("");
  const [timeframe, setTimeframe] = useState("1d");

  const [run, setRun] = useState<Run | null>(null);
  const [equity, setEquity] = useState<EquityPoint[]>([]);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void refreshDatasets();
    api
      .listStrategies()
      .then((s) => {
        setStrategies(s);
        if (s[0]) selectStrategy(s[0]);
      })
      .catch((e) => setError(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function refreshDatasets() {
    try {
      const { items } = await api.listDatasets();
      setDatasets(items);
      if (items[0] && !datasetId) setDatasetId(items[0].id);
    } catch (e) {
      setError(String(e));
    }
  }

  function selectStrategy(s: Strategy) {
    setStrategyName(s.name);
    const init: Record<string, number> = {};
    for (const p of s.params) if (typeof p.default === "number") init[p.name] = p.default;
    setParams(init);
  }

  async function seedDemo() {
    setBusy(true);
    setError(null);
    try {
      const ds = await api.createDataset({
        name: `Demo sintético ${new Date().toLocaleString()}`,
        timeframe: "1d",
        candles: syntheticCandles(),
      });
      await refreshDatasets();
      setDatasetId(ds.id);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function uploadCsv(file: File) {
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("name", file.name.replace(/\.csv$/i, "") || "CSV");
      form.append("timeframe", timeframe.trim() || "1d");
      if (symbol.trim()) form.append("symbol", symbol.trim());
      const ds = await api.uploadCsv(form);
      await refreshDatasets();
      setDatasetId(ds.id);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  function downloadSample() {
    const blob = new Blob([candlesToCsv(syntheticCandles())], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ohlcv-ejemplo.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function loadResults(runId: string) {
    const [eq, tr] = await Promise.all([api.equity(runId), api.trades(runId)]);
    setEquity(eq);
    setTrades(tr.items);
  }

  async function launch() {
    setBusy(true);
    setError(null);
    setRun(null);
    setEquity([]);
    setTrades([]);
    try {
      const r = await api.runBacktest({
        dataset_id: datasetId,
        strategy: strategyName,
        params,
        initial_capital: capital,
        commission_bps: commissionBps,
      });
      setRun(r);
      await loadResults(r.id);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  // Open a past run (from the Corridas view) in the results panel.
  async function openRun(runId: string) {
    setView("backtest");
    setBusy(true);
    setError(null);
    try {
      const r = await api.getRun(runId);
      setRun(r);
      await loadResults(runId);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  const strategy = strategies.find((s) => s.name === strategyName);
  const m: Metrics | undefined = run?.metrics;

  return (
    <AppShell active={view} onNavigate={setView}>
      {error && (
        <p className="mb-5 rounded border border-neg/40 bg-neg/10 p-3 text-sm text-neg">{error}</p>
      )}

      {view === "runs" ? (
        <RunsView onSelect={openRun} />
      ) : (
        <div className="mx-auto max-w-5xl space-y-5">
          {/* Dataset */}
          <section className="rounded-xl border border-border bg-surface p-5">
            <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold">
              <Step n={1} /> Dataset
            </h2>

            <div className="flex items-center gap-2">
              {datasets.length > 0 && (
                <select
                  value={datasetId}
                  onChange={(e) => setDatasetId(e.target.value)}
                  className={`${INPUT} flex-1`}
                >
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                      {d.symbol ? ` · ${d.symbol}` : ""} · {d.timeframe}
                    </option>
                  ))}
                </select>
              )}
              <button
                onClick={seedDemo}
                disabled={busy}
                className="shrink-0 rounded border border-border bg-surface-2 px-3 py-1.5 text-sm text-fg transition hover:border-accent/60 disabled:opacity-50"
              >
                + Dataset de ejemplo
              </button>
            </div>
            {datasets.length === 0 && (
              <p className="mt-2 text-sm text-muted">
                No hay datasets. Genera uno de ejemplo o sube un CSV abajo.
              </p>
            )}

            {/* Upload CSV */}
            <div className="mt-4 rounded-lg border border-dashed border-border bg-surface-2/40 p-4">
              <div className="mb-3 flex items-center justify-between">
                <span className="text-sm font-medium">Subir CSV (instrumento real)</span>
                <button onClick={downloadSample} className="text-xs text-accent hover:underline">
                  descargar CSV de ejemplo
                </button>
              </div>
              <div className="flex flex-wrap items-end gap-3">
                <label className="text-xs text-muted">
                  símbolo
                  <input
                    value={symbol}
                    onChange={(e) => setSymbol(e.target.value)}
                    placeholder="AAPL"
                    className={`${INPUT} mt-1 block w-28`}
                  />
                </label>
                <label className="text-xs text-muted">
                  timeframe
                  <input
                    value={timeframe}
                    onChange={(e) => setTimeframe(e.target.value)}
                    placeholder="1d"
                    className={`${INPUT} mt-1 block w-20`}
                  />
                </label>
                <input
                  type="file"
                  accept=".csv,text/csv"
                  disabled={busy}
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) void uploadCsv(f);
                    e.target.value = "";
                  }}
                  className="text-sm text-muted file:mr-2 file:rounded file:border file:border-border file:bg-surface-2 file:px-2 file:py-1 file:text-sm file:text-fg"
                />
              </div>
              <p className="mt-2 text-xs text-muted">
                Columnas: <code className="text-fg">timestamp,open,high,low,close,volume</code> ·
                timestamp ISO-8601 UTC.
              </p>
            </div>
          </section>

          {/* Estrategia */}
          <section className="rounded-xl border border-border bg-surface p-5">
            <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold">
              <Step n={2} /> Estrategia
            </h2>
            <select
              value={strategyName}
              onChange={(e) => {
                const s = strategies.find((x) => x.name === e.target.value);
                if (s) selectStrategy(s);
              }}
              className={`${INPUT} w-full`}
            >
              {strategies.map((s) => (
                <option key={s.name} value={s.name}>
                  {s.name}
                </option>
              ))}
            </select>
            {strategy && <p className="mt-2 text-xs text-muted">{strategy.description}</p>}

            <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {strategy?.params.map((p) => (
                <label key={p.name} className="text-xs text-muted">
                  {p.name}
                  <input
                    type="number"
                    value={params[p.name] ?? ""}
                    onChange={(e) =>
                      setParams((prev) => ({ ...prev, [p.name]: Number(e.target.value) }))
                    }
                    className={`${INPUT} nums mt-1 block w-full`}
                  />
                </label>
              ))}
              <label className="text-xs text-muted">
                capital inicial
                <input
                  type="number"
                  value={capital}
                  onChange={(e) => setCapital(Number(e.target.value))}
                  className={`${INPUT} nums mt-1 block w-full`}
                />
              </label>
              <label className="text-xs text-muted">
                comisión (bps)
                <input
                  type="number"
                  value={commissionBps}
                  onChange={(e) => setCommissionBps(Number(e.target.value))}
                  className={`${INPUT} nums mt-1 block w-full`}
                />
              </label>
            </div>

            <button
              onClick={launch}
              disabled={busy || !datasetId || !strategyName}
              className="mt-5 inline-flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition hover:brightness-110 disabled:opacity-50"
            >
              {busy && (
                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/40 border-t-white" />
              )}
              {busy ? "Corriendo…" : "Lanzar backtest"}
            </button>
          </section>

          {/* Resultados */}
          {run && m && (
            <section className="rounded-xl border border-border bg-surface p-5">
              <h2 className="mb-4 text-sm font-semibold">Resultados</h2>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                <Stat label="Retorno total" value={pct(run.total_return)} tone={run.total_return} />
                <Stat label="Equity final" value={run.final_equity.toFixed(2)} />
                <Stat
                  label="Max drawdown"
                  value={`-${(m.max_drawdown * 100).toFixed(2)}%`}
                  tone={-1}
                />
                <Stat label="Sharpe" value={num(m.sharpe)} />
                <Stat label="Trades" value={String(m.n_trades)} />
                <Stat label="Win rate" value={m.win_rate === null ? "—" : pct(m.win_rate)} />
                <Stat label="Profit factor" value={num(m.profit_factor)} />
                <Stat label="Expectancy" value={num(m.expectancy)} />
              </div>

              <h3 className="mb-2 mt-6 text-xs font-medium uppercase tracking-wide text-muted">
                Curva de equity
              </h3>
              <div className="rounded-lg border border-border bg-surface-2/30 p-2">
                <EquityChart points={equity} />
              </div>

              <h3 className="mb-2 mt-6 text-xs font-medium uppercase tracking-wide text-muted">
                Operaciones ({trades.length})
              </h3>
              <TradesTable trades={trades} />
            </section>
          )}
        </div>
      )}
    </AppShell>
  );
}

function Step({ n }: { n: number }) {
  return (
    <span className="grid h-5 w-5 place-items-center rounded bg-accent/15 text-[11px] font-semibold text-accent">
      {n}
    </span>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: number }) {
  const color = tone === undefined ? "text-fg" : tone >= 0 ? "text-pos" : "text-neg";
  return (
    <div className="rounded-lg border border-border bg-surface-2/40 p-3">
      <div className="text-[11px] uppercase tracking-wide text-muted">{label}</div>
      <div className={`nums mt-1 text-lg font-semibold ${color}`}>{value}</div>
    </div>
  );
}
