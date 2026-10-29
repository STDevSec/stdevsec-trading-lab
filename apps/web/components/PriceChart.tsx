"use client";

import { useEffect, useRef, useState } from "react";
import {
  createChart,
  type IChartApi,
  type ISeriesApi,
  type LogicalRange,
  type UTCTimestamp,
} from "lightweight-charts";
import type { Ohlcv } from "@/lib/api";

type LineDatum = { time: UTCTimestamp; value: number };

// Build a lightweight-charts line series from an index-aligned indicator array,
// dropping null (warm-up / undefined) points.
function line(times: number[], values: (number | null)[]): LineDatum[] {
  const out: LineDatum[] = [];
  for (let i = 0; i < values.length; i++) {
    const v = values[i];
    if (v !== null) out.push({ time: times[i] as UTCTimestamp, value: v });
  }
  return out;
}

const BASE_LAYOUT = {
  layout: { background: { color: "transparent" }, textColor: "#7d8aa0" },
  grid: {
    horzLines: { color: "rgba(35,44,64,0.6)" },
    vertLines: { color: "rgba(35,44,64,0.6)" },
  },
  rightPriceScale: { borderColor: "#232c40" },
  timeScale: { borderColor: "#232c40", timeVisible: false },
  crosshair: { vertLine: { color: "#4c8dff" }, horzLine: { color: "#4c8dff" } },
} as const;

// Keep several charts' time axes in sync (one visible range drives the others).
function syncTimeScales(charts: IChartApi[]) {
  let guard = false;
  for (const src of charts) {
    src.timeScale().subscribeVisibleLogicalRangeChange((range: LogicalRange | null) => {
      if (guard || !range) return;
      guard = true;
      for (const dst of charts) if (dst !== src) dst.timeScale().setVisibleLogicalRange(range);
      guard = false;
    });
  }
}

const TOGGLES = [
  { key: "sma20", label: "SMA 20", color: "#4c8dff" },
  { key: "sma50", label: "SMA 50", color: "#f0b90b" },
  { key: "ema20", label: "EMA 20", color: "#c678dd" },
  { key: "bb", label: "Bollinger", color: "#7d8aa0" },
  { key: "rsi", label: "RSI 14", color: "#4c8dff" },
  { key: "macd", label: "MACD", color: "#4c8dff" },
] as const;
type ToggleKey = (typeof TOGGLES)[number]["key"];

export default function PriceChart({ data }: { data: Ohlcv }) {
  const priceRef = useRef<HTMLDivElement>(null);
  const rsiRef = useRef<HTMLDivElement>(null);
  const macdRef = useRef<HTMLDivElement>(null);
  const [on, setOn] = useState<Record<ToggleKey, boolean>>({
    sma20: true,
    sma50: false,
    ema20: false,
    bb: true,
    rsi: true,
    macd: true,
  });

  useEffect(() => {
    const priceEl = priceRef.current;
    if (!priceEl) return;
    const times = data.candles.map((c) => c.time);
    const ind = data.indicators;
    const charts: IChartApi[] = [];

    // --- Price + overlays ---
    const price = createChart(priceEl, { height: 320, autoSize: true, ...BASE_LAYOUT });
    charts.push(price);
    const candles = price.addCandlestickSeries({
      upColor: "#2ebd85",
      downColor: "#f6465d",
      borderVisible: false,
      wickUpColor: "#2ebd85",
      wickDownColor: "#f6465d",
    });
    candles.setData(
      data.candles.map((c) => ({
        time: c.time as UTCTimestamp,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
      })),
    );
    const overlay = (key: ToggleKey, values: (number | null)[], color: string, dashed = false) => {
      if (!on[key]) return;
      const s: ISeriesApi<"Line"> = price.addLineSeries({
        color,
        lineWidth: 1,
        lineStyle: dashed ? 2 : 0,
        priceLineVisible: false,
        lastValueVisible: false,
      });
      s.setData(line(times, values));
    };
    overlay("sma20", ind.sma20 ?? [], "#4c8dff");
    overlay("sma50", ind.sma50 ?? [], "#f0b90b");
    overlay("ema20", ind.ema20 ?? [], "#c678dd");
    if (on.bb) {
      overlay("bb", ind.bb_upper ?? [], "#7d8aa0");
      overlay("bb", ind.bb_mid ?? [], "#7d8aa0", true);
      overlay("bb", ind.bb_lower ?? [], "#7d8aa0");
    }
    price.timeScale().fitContent();

    // --- RSI pane ---
    if (on.rsi && rsiRef.current) {
      const rsi = createChart(rsiRef.current, { height: 120, autoSize: true, ...BASE_LAYOUT });
      charts.push(rsi);
      const s = rsi.addLineSeries({ color: "#4c8dff", lineWidth: 1, lastValueVisible: false });
      s.setData(line(times, ind.rsi14 ?? []));
      for (const level of [70, 30]) {
        s.createPriceLine({
          price: level,
          color: "#232c40",
          lineWidth: 1,
          lineStyle: 2,
          axisLabelVisible: true,
          title: "",
        });
      }
      rsi.timeScale().fitContent();
    }

    // --- MACD pane ---
    if (on.macd && macdRef.current) {
      const m = createChart(macdRef.current, { height: 120, autoSize: true, ...BASE_LAYOUT });
      charts.push(m);
      const hist = m.addHistogramSeries({ priceLineVisible: false, lastValueVisible: false });
      hist.setData(
        line(times, ind.macd_hist ?? []).map((d) => ({
          time: d.time,
          value: d.value,
          color: d.value >= 0 ? "rgba(46,189,133,0.6)" : "rgba(246,70,93,0.6)",
        })),
      );
      const ml = m.addLineSeries({ color: "#4c8dff", lineWidth: 1, lastValueVisible: false });
      ml.setData(line(times, ind.macd ?? []));
      const sl = m.addLineSeries({ color: "#f6465d", lineWidth: 1, lastValueVisible: false });
      sl.setData(line(times, ind.macd_signal ?? []));
      m.timeScale().fitContent();
    }

    syncTimeScales(charts);
    return () => charts.forEach((c) => c.remove());
  }, [data, on]);

  return (
    <div>
      <div className="mb-3 flex flex-wrap gap-2">
        {TOGGLES.map((t) => (
          <button
            key={t.key}
            onClick={() => setOn((p) => ({ ...p, [t.key]: !p[t.key] }))}
            className={`flex items-center gap-1.5 rounded border px-2 py-1 text-xs transition ${
              on[t.key]
                ? "border-border bg-surface-2 text-fg"
                : "border-transparent text-muted hover:text-fg"
            }`}
          >
            <span className="h-2 w-2 rounded-full" style={{ background: t.color }} />
            {t.label}
          </button>
        ))}
      </div>
      <div ref={priceRef} className="w-full" />
      {on.rsi && (
        <>
          <div className="mt-2 text-[11px] uppercase tracking-wide text-muted">RSI 14</div>
          <div ref={rsiRef} className="w-full" />
        </>
      )}
      {on.macd && (
        <>
          <div className="mt-2 text-[11px] uppercase tracking-wide text-muted">MACD 12/26/9</div>
          <div ref={macdRef} className="w-full" />
        </>
      )}
    </div>
  );
}
