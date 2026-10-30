"use client";

import { useEffect, useRef, useState } from "react";
import { createChart, type ISeriesApi, type UTCTimestamp } from "lightweight-charts";
import { api, type OhlcvCandle } from "@/lib/api";

const INTERVALS = ["1m", "5m", "15m", "1h", "4h", "1d"] as const;

/**
 * Candlestick chart of the selected symbol from Binance (public klines).
 * The last candle's close follows the live price polled by the parent, so the
 * chart ticks without refetching the whole series.
 */
export default function LiveChart({
  symbol,
  livePrice,
  height = 320,
}: {
  symbol: string;
  livePrice?: number;
  height?: number;
}) {
  const el = useRef<HTMLDivElement>(null);
  const series = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const last = useRef<OhlcvCandle | null>(null);
  const [interval, setInterval_] = useState<(typeof INTERVALS)[number]>("1m");
  const [error, setError] = useState<string | null>(null);

  // (Re)create chart + load candles when symbol or interval changes.
  useEffect(() => {
    const node = el.current;
    if (!node) return;
    const chart = createChart(node, {
      height,
      autoSize: true,
      layout: { background: { color: "transparent" }, textColor: "#7d8aa0" },
      grid: {
        horzLines: { color: "rgba(35,44,64,0.6)" },
        vertLines: { color: "rgba(35,44,64,0.6)" },
      },
      rightPriceScale: { borderColor: "#232c40" },
      timeScale: { borderColor: "#232c40", timeVisible: true },
      crosshair: { vertLine: { color: "#4c8dff" }, horzLine: { color: "#4c8dff" } },
    });
    const s = chart.addCandlestickSeries({
      upColor: "#2ebd85",
      downColor: "#f6465d",
      borderVisible: false,
      wickUpColor: "#2ebd85",
      wickDownColor: "#f6465d",
    });
    series.current = s;
    let alive = true;
    setError(null);
    api
      .paperKlines(symbol, interval)
      .then((candles) => {
        if (!alive) return;
        s.setData(
          candles.map((c) => ({
            time: c.time as UTCTimestamp,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
          })),
        );
        last.current = candles[candles.length - 1] ?? null;
        chart.timeScale().fitContent();
      })
      .catch((e) => alive && setError(String(e)));
    return () => {
      alive = false;
      series.current = null;
      last.current = null;
      chart.remove();
    };
  }, [symbol, interval, height]);

  // Live tick: move the last candle's close (and high/low) to the current price.
  useEffect(() => {
    const s = series.current;
    const c = last.current;
    if (!s || !c || !livePrice) return;
    c.close = livePrice;
    c.high = Math.max(c.high, livePrice);
    c.low = Math.min(c.low, livePrice);
    s.update({ time: c.time as UTCTimestamp, open: c.open, high: c.high, low: c.low, close: c.close });
  }, [livePrice]);

  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-1.5">
        {INTERVALS.map((iv) => (
          <button
            key={iv}
            onClick={() => setInterval_(iv)}
            className={`rounded border px-2 py-1 text-xs transition ${
              interval === iv
                ? "border-border bg-surface-2 text-fg"
                : "border-transparent text-muted hover:text-fg"
            }`}
          >
            {iv}
          </button>
        ))}
      </div>
      {error ? (
        <p className="rounded border border-neg/40 bg-neg/10 p-3 text-sm text-neg">{error}</p>
      ) : (
        <div ref={el} className="w-full" />
      )}
    </div>
  );
}
