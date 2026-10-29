/**
 * Typed client for the STDevsec Trading Lab API.
 *
 * Every response is validated with Zod before use — the backend is treated as
 * untrusted input, same as the synthetic data file. The base URL comes from
 * NEXT_PUBLIC_API_URL (default the local dev API).
 */
import { z } from "zod";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// --- Response schemas -------------------------------------------------------
export const DatasetSchema = z.object({
  id: z.string(),
  name: z.string(),
  symbol: z.string().nullable(),
  timeframe: z.string(),
  created_at: z.string(),
});
export type Dataset = z.infer<typeof DatasetSchema>;

const page = <T extends z.ZodTypeAny>(item: T) =>
  z.object({ items: z.array(item), total: z.number(), limit: z.number(), offset: z.number() });

export const StrategyParamSchema = z.object({
  name: z.string(),
  type: z.string(),
  default: z.unknown(),
  description: z.string(),
});
export const StrategySchema = z.object({
  name: z.string(),
  description: z.string(),
  params: z.array(StrategyParamSchema),
});
export type Strategy = z.infer<typeof StrategySchema>;
export type StrategyParam = z.infer<typeof StrategyParamSchema>;

export const MetricsSchema = z.object({
  n_trades: z.number(),
  win_rate: z.number().nullable(),
  profit_factor: z.number().nullable(),
  expectancy: z.number().nullable(),
  avg_win: z.number().nullable(),
  avg_loss: z.number().nullable(),
  net_profit: z.number(),
  total_return: z.number(),
  max_drawdown: z.number(),
  sharpe: z.number().nullable(),
  max_consecutive_wins: z.number(),
  max_consecutive_losses: z.number(),
});
export type Metrics = z.infer<typeof MetricsSchema>;

export const RunSchema = z.object({
  id: z.string(),
  strategy_name: z.string(),
  params: z.record(z.unknown()),
  initial_capital: z.number(),
  status: z.string(),
  final_equity: z.number(),
  total_return: z.number(),
  metrics: MetricsSchema,
  created_at: z.string(),
});
export type Run = z.infer<typeof RunSchema>;

export const EquityPointSchema = z.object({ timestamp: z.string(), equity: z.number() });
export type EquityPoint = z.infer<typeof EquityPointSchema>;

export const TradeSchema = z.object({
  entry_time: z.string(),
  exit_time: z.string(),
  units: z.number(),
  entry_price: z.number(),
  exit_price: z.number(),
  pnl: z.number(),
  return_pct: z.number(),
});
export type Trade = z.infer<typeof TradeSchema>;

// --- Fetch helper -----------------------------------------------------------
async function call<T>(path: string, schema: z.ZodType<T>, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    // The API uses a single error envelope: {error: {code, message, details}}.
    const msg = body?.error?.message ?? body?.detail ?? `HTTP ${res.status}`;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return schema.parse(body);
}

async function upload(path: string, form: FormData): Promise<Dataset> {
  const res = await fetch(`${BASE}${path}`, { method: "POST", body: form });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(body?.error?.message ?? `HTTP ${res.status}`);
  return DatasetSchema.parse(body);
}

export const api = {
  listDatasets: () => call("/api/v1/datasets?limit=200", page(DatasetSchema)),
  createDataset: (payload: unknown) =>
    call("/api/v1/datasets", DatasetSchema, { method: "POST", body: JSON.stringify(payload) }),
  uploadCsv: (form: FormData) => upload("/api/v1/datasets/upload", form),
  listStrategies: () => call("/api/v1/strategies", z.array(StrategySchema)),
  runBacktest: (payload: unknown) =>
    call("/api/v1/backtests", RunSchema, { method: "POST", body: JSON.stringify(payload) }),
  listBacktests: () => call("/api/v1/backtests?limit=100", page(RunSchema)),
  getRun: (runId: string) => call(`/api/v1/backtests/${runId}`, RunSchema),
  equity: (runId: string) =>
    call(`/api/v1/backtests/${runId}/equity`, z.array(EquityPointSchema)),
  trades: (runId: string) =>
    call(`/api/v1/backtests/${runId}/trades?limit=200`, page(TradeSchema)),
};

/**
 * A small deterministic GBM series to seed a demo dataset from the browser,
 * so the UI is usable without running the CLI seeder. Not the engine's model —
 * just enough candles to drive a backtest.
 */
export function syntheticCandles(rows = 180, seed = 42) {
  let s = seed >>> 0;
  const rand = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 0xffffffff); // LCG, uniform [0,1)
  const candles = [];
  let price = 100;
  const start = Date.UTC(2024, 0, 1) / 1000;
  for (let i = 0; i < rows; i++) {
    const drift = 0.0002;
    const ret = drift + (rand() - 0.5) * 0.04; // ~2% daily vol
    const open = price;
    const close = Math.max(1, open * (1 + ret));
    const high = Math.max(open, close) * (1 + rand() * 0.01);
    const low = Math.min(open, close) * (1 - rand() * 0.01);
    candles.push({
      timestamp: new Date((start + i * 86400) * 1000).toISOString(),
      open: +open.toFixed(4),
      high: +high.toFixed(4),
      low: +low.toFixed(4),
      close: +close.toFixed(4),
      volume: Math.round(1000 + rand() * 9000),
    });
    price = close;
  }
  return candles;
}

/** Serialize candles to an OHLCV CSV string (the upload format), for a sample download. */
export function candlesToCsv(candles: ReturnType<typeof syntheticCandles>): string {
  const head = "timestamp,open,high,low,close,volume";
  const rows = candles.map(
    (c) => `${c.timestamp},${c.open},${c.high},${c.low},${c.close},${c.volume}`,
  );
  return [head, ...rows].join("\n") + "\n";
}
