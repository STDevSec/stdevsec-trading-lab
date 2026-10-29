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
      layout: { background: { color: "transparent" }, textColor: "#7d8aa0" },
      grid: {
        horzLines: { color: "rgba(35,44,64,0.6)" },
        vertLines: { color: "rgba(35,44,64,0.6)" },
      },
      rightPriceScale: { borderColor: "#232c40" },
      timeScale: { timeVisible: false, borderColor: "#232c40" },
      crosshair: { vertLine: { color: "#4c8dff" }, horzLine: { color: "#4c8dff" } },
    });
    const series = chart.addLineSeries({
      color: "#4c8dff",
      lineWidth: 2,
      priceLineColor: "#4c8dff",
    });
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
