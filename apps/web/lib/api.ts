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

export const OhlcvCandleSchema = z.object({
  time: z.number(),
  open: z.number(),
  high: z.number(),
  low: z.number(),
  close: z.number(),
  volume: z.number(),
});
export const OhlcvSchema = z.object({
  candles: z.array(OhlcvCandleSchema),
  indicators: z.record(z.array(z.number().nullable())),
});
export type Ohlcv = z.infer<typeof OhlcvSchema>;
export type OhlcvCandle = z.infer<typeof OhlcvCandleSchema>;

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

export const JournalImageSchema = z.object({
  id: z.string(),
  filename: z.string(),
  content_type: z.string(),
  created_at: z.string(),
});
export const JournalEntrySchema = z.object({
  id: z.string(),
  title: z.string(),
  notes: z.string(),
  tags: z.array(z.string()),
  run_id: z.string().nullable(),
  created_at: z.string(),
});
export const JournalDetailSchema = JournalEntrySchema.extend({
  images: z.array(JournalImageSchema),
});
export type JournalEntry = z.infer<typeof JournalEntrySchema>;
export type JournalDetail = z.infer<typeof JournalDetailSchema>;
export type JournalImage = z.infer<typeof JournalImageSchema>;

export const PaperPositionSchema = z.object({
  symbol: z.string(),
  qty: z.number(),
  avg_price: z.number(),
});
export const PaperAccountSchema = z.object({
  id: z.string(),
  name: z.string(),
  cash: z.number(),
  created_at: z.string(),
});
export const PaperAccountDetailSchema = PaperAccountSchema.extend({
  positions: z.array(PaperPositionSchema),
});
export const PaperOrderSchema = z.object({
  id: z.string(),
  symbol: z.string(),
  side: z.string(),
  qty: z.number(),
  price: z.number(),
  created_at: z.string(),
});
export const PriceSchema = z.object({ symbol: z.string(), price: z.number() });
export type PaperAccount = z.infer<typeof PaperAccountSchema>;
export type PaperAccountDetail = z.infer<typeof PaperAccountDetailSchema>;
export type PaperPosition = z.infer<typeof PaperPositionSchema>;
export type PaperOrder = z.infer<typeof PaperOrderSchema>;

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

async function upload<T>(path: string, form: FormData, schema: z.ZodType<T>): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: "POST", body: form });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(body?.error?.message ?? `HTTP ${res.status}`);
  return schema.parse(body);
}

export const api = {
  listDatasets: () => call("/api/v1/datasets?limit=200", page(DatasetSchema)),
  createDataset: (payload: unknown) =>
    call("/api/v1/datasets", DatasetSchema, { method: "POST", body: JSON.stringify(payload) }),
  uploadCsv: (form: FormData) => upload("/api/v1/datasets/upload", form, DatasetSchema),
  ohlcv: (datasetId: string) => call(`/api/v1/datasets/${datasetId}/ohlcv`, OhlcvSchema),
  listStrategies: () => call("/api/v1/strategies", z.array(StrategySchema)),
  runBacktest: (payload: unknown) =>
    call("/api/v1/backtests", RunSchema, { method: "POST", body: JSON.stringify(payload) }),
  listBacktests: () => call("/api/v1/backtests?limit=100", page(RunSchema)),
  getRun: (runId: string) => call(`/api/v1/backtests/${runId}`, RunSchema),
  equity: (runId: string) =>
    call(`/api/v1/backtests/${runId}/equity`, z.array(EquityPointSchema)),
  trades: (runId: string) =>
    call(`/api/v1/backtests/${runId}/trades?limit=200`, page(TradeSchema)),

  // Journal
  listJournal: () => call("/api/v1/journal/entries?limit=100", page(JournalEntrySchema)),
  getJournalEntry: (id: string) =>
    call(`/api/v1/journal/entries/${id}`, JournalDetailSchema),
  createJournalEntry: (payload: unknown) =>
    call("/api/v1/journal/entries", JournalEntrySchema, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  uploadJournalImage: (entryId: string, form: FormData) =>
    upload(`/api/v1/journal/entries/${entryId}/images`, form, JournalImageSchema),
  deleteJournalEntry: async (id: string) => {
    const res = await fetch(`${BASE}/api/v1/journal/entries/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
  },
  journalImageUrl: (entryId: string, imageId: string) =>
    `${BASE}/api/v1/journal/entries/${entryId}/images/${imageId}`,

  // Paper trading
  listPaperAccounts: () => call("/api/v1/paper/accounts?limit=100", page(PaperAccountSchema)),
  createPaperAccount: (payload: unknown) =>
    call("/api/v1/paper/accounts", PaperAccountSchema, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  getPaperAccount: (id: string) =>
    call(`/api/v1/paper/accounts/${id}`, PaperAccountDetailSchema),
  placePaperOrder: (accountId: string, payload: unknown) =>
    call(`/api/v1/paper/accounts/${accountId}/orders`, PaperOrderSchema, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  listPaperOrders: (accountId: string) =>
    call(`/api/v1/paper/accounts/${accountId}/orders?limit=100`, page(PaperOrderSchema)),
  paperPrice: (symbol: string) =>
    call(`/api/v1/paper/price?symbol=${encodeURIComponent(symbol)}`, PriceSchema),
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
