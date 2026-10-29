"use client";

import { useEffect, useRef, useState } from "react";
import { createChart, type IChartApi, type UTCTimestamp } from "lightweight-charts";
import { CandleSeriesSchema, type CandleSeries } from "@stdevsec/shared-contracts";

/**
 * Renders a candlestick chart of the synthetic OHLCV dataset.
 * The fetched JSON is validated with the shared Zod schema before use — even
 * our own data file is treated as untrusted input.
 */
export default function OhlcvChart() {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [count, setCount] = useState(0);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let chart: IChartApi | null = null;
    let disposed = false;

    const load = async () => {
      try {
        const res = await fetch("/sample-ohlcv.json");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: CandleSeries = CandleSeriesSchema.parse(await res.json());
        if (disposed) return;

        chart = createChart(container, {
          height: 400,
          autoSize: true,
          layout: { background: { color: "transparent" }, textColor: "#888" },
          grid: {
            horzLines: { color: "rgba(128,128,128,0.1)" },
            vertLines: { color: "rgba(128,128,128,0.1)" },
          },
          timeScale: { timeVisible: true },
        });
        const series = chart.addCandlestickSeries();
        series.setData(
          data.map((c) => ({
            time: c.time as UTCTimestamp,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
          })),
        );
        chart.timeScale().fitContent();
        setCount(data.length);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      }
    };

    void load();

    return () => {
      disposed = true;
      chart?.remove();
    };
  }, []);

  return (
    <div>
      {error && (
        <p className="text-sm text-red-600">
          No se pudo cargar el dataset sintético: {error}. Genéralo con{" "}
          <code>uv run python scripts/gen_sample.py</code>.
        </p>
      )}
      <div ref={containerRef} className="w-full" />
      {count > 0 && (
        <p className="mt-2 text-xs text-neutral-500">
          {count} velas sintéticas · datos simulados con semilla fija · no es desempeño real.
        </p>
      )}
    </div>
  );
}
