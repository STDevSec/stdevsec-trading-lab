"use client";

import { useEffect, useState } from "react";
import {
  api,
  syntheticCandles,
  type Dataset,
  type EquityPoint,
  type Metrics,
  type Run,
  type Strategy,
} from "@/lib/api";
import EquityChart from "@/components/EquityChart";

const pct = (x: number) => `${(x * 100).toFixed(2)}%`;
const num = (x: number | null, d = 2) => (x === null ? "—" : x.toFixed(d));

export default function TradingLab() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [datasetId, setDatasetId] = useState("");
  const [strategyName, setStrategyName] = useState("");
  const [params, setParams] = useState<Record<string, number>>({});
  const [capital, setCapital] = useState(10000);
  const [commissionBps, setCommissionBps] = useState(0);

  const [run, setRun] = useState<Run | null>(null);
  const [equity, setEquity] = useState<EquityPoint[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load catalogs on mount.
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

  async function launch() {
    setBusy(true);
    setError(null);
    setRun(null);
    setEquity([]);
    try {
      const r = await api.runBacktest({
        dataset_id: datasetId,
        strategy: strategyName,
        params,
        initial_capital: capital,
        commission_bps: commissionBps,
      });
      setRun(r);
      setEquity(await api.equity(r.id));
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  const strategy = strategies.find((s) => s.name === strategyName);
  const m: Metrics | undefined = run?.metrics;

  return (
    <div className="space-y-8">
      {error && (
        <p className="rounded border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {/* Dataset */}
      <section>
        <div className="mb-2 flex items-center justify-between">
          <h2 className="text-lg font-medium">1 · Dataset</h2>
          <button
            onClick={seedDemo}
            disabled={busy}
            className="rounded border px-3 py-1 text-sm hover:bg-neutral-100 disabled:opacity-50"
          >
            + Generar dataset de ejemplo
          </button>
        </div>
        {datasets.length === 0 ? (
          <p className="text-sm text-neutral-500">
            No hay datasets. Genera uno de ejemplo o crea uno vía la API.
          </p>
        ) : (
          <select
            value={datasetId}
            onChange={(e) => setDatasetId(e.target.value)}
            className="w-full rounded border bg-transparent p-2 text-sm"
          >
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} · {d.timeframe}
              </option>
            ))}
          </select>
        )}
      </section>

      {/* Strategy + params */}
      <section>
        <h2 className="mb-2 text-lg font-medium">2 · Estrategia</h2>
        <select
          value={strategyName}
          onChange={(e) => {
            const s = strategies.find((x) => x.name === e.target.value);
            if (s) selectStrategy(s);
          }}
          className="w-full rounded border bg-transparent p-2 text-sm"
        >
          {strategies.map((s) => (
            <option key={s.name} value={s.name}>
              {s.name}
            </option>
          ))}
        </select>
        {strategy && <p className="mt-1 text-xs text-neutral-500">{strategy.description}</p>}

        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {strategy?.params.map((p) => (
            <label key={p.name} className="text-sm">
              <span className="block text-neutral-500">{p.name}</span>
              <input
                type="number"
                value={params[p.name] ?? ""}
                onChange={(e) =>
                  setParams((prev) => ({ ...prev, [p.name]: Number(e.target.value) }))
                }
                className="mt-1 w-full rounded border bg-transparent p-1"
              />
            </label>
          ))}
          <label className="text-sm">
            <span className="block text-neutral-500">capital inicial</span>
            <input
              type="number"
              value={capital}
              onChange={(e) => setCapital(Number(e.target.value))}
              className="mt-1 w-full rounded border bg-transparent p-1"
            />
          </label>
          <label className="text-sm">
            <span className="block text-neutral-500">comisión (bps)</span>
            <input
              type="number"
              value={commissionBps}
              onChange={(e) => setCommissionBps(Number(e.target.value))}
              className="mt-1 w-full rounded border bg-transparent p-1"
            />
          </label>
        </div>

        <button
          onClick={launch}
          disabled={busy || !datasetId || !strategyName}
          className="mt-4 rounded bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {busy ? "Corriendo…" : "3 · Lanzar backtest"}
        </button>
      </section>

      {/* Results */}
      {run && m && (
        <section>
          <h2 className="mb-2 text-lg font-medium">Resultados</h2>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Stat label="Retorno total" value={pct(run.total_return)} />
            <Stat label="Equity final" value={run.final_equity.toFixed(2)} />
            <Stat label="Max drawdown" value={pct(m.max_drawdown)} />
            <Stat label="Sharpe" value={num(m.sharpe)} />
            <Stat label="Trades" value={String(m.n_trades)} />
            <Stat label="Win rate" value={m.win_rate === null ? "—" : pct(m.win_rate)} />
            <Stat label="Profit factor" value={num(m.profit_factor)} />
            <Stat label="Expectancy" value={num(m.expectancy)} />
          </div>
          <div className="mt-4">
            <h3 className="mb-1 text-sm font-medium text-neutral-500">Curva de equity</h3>
            <EquityChart points={equity} />
          </div>
        </section>
      )}

      <p className="text-xs text-neutral-400">
        Solo simulación · no es asesoría financiera ni desempeño real de mercado.
      </p>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded border p-2">
      <div className="text-xs text-neutral-500">{label}</div>
      <div className="text-base font-semibold tabular-nums">{value}</div>
    </div>
  );
}
