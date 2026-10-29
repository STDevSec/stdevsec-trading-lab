"use client";

import { useEffect, useRef } from "react";
import { createChart, type IChartApi, type UTCTimestamp } from "lightweight-charts";
import type { EquityPoint } from "@/lib/api";

/** Line chart of a backtest's equity curve. Timestamps are ISO strings → seconds. */
export default function EquityChart({ points }: { points: EquityPoint[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || points.length === 0) return;

    const chart: IChartApi = createChart(container, {
      height: 320,
      autoSize: true,
      layout: { background: { color: "transparent" }, textColor: "#888" },
      grid: {
        horzLines: { color: "rgba(128,128,128,0.1)" },
        vertLines: { color: "rgba(128,128,128,0.1)" },
      },
      timeScale: { timeVisible: false },
    });
    const series = chart.addLineSeries({ color: "#2563eb", lineWidth: 2 });
    series.setData(
      points.map((p) => ({
        time: Math.floor(Date.parse(p.timestamp) / 1000) as UTCTimestamp,
        value: p.equity,
      })),
    );
    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [points]);

  return <div ref={containerRef} className="w-full" />;
}
