import { z } from "zod";

/**
 * A single OHLCV candle as consumed by the frontend chart.
 * `time` is a Unix timestamp in **seconds** (UTC), matching lightweight-charts.
 */
export const CandleSchema = z
  .object({
    time: z.number().int().nonnegative(),
    open: z.number().positive(),
    high: z.number().positive(),
    low: z.number().positive(),
    close: z.number().positive(),
    volume: z.number().nonnegative(),
  })
  .refine((c) => c.high >= Math.max(c.open, c.close, c.low), {
    message: "high must be >= max(open, close, low)",
  })
  .refine((c) => c.low <= Math.min(c.open, c.close, c.high), {
    message: "low must be <= min(open, close, high)",
  });

export const CandleSeriesSchema = z.array(CandleSchema);

export type Candle = z.infer<typeof CandleSchema>;
export type CandleSeries = z.infer<typeof CandleSeriesSchema>;
