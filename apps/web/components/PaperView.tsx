"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  api,
  type PaperAccount,
  type PaperAccountDetail,
  type PaperOrder,
} from "@/lib/api";
import LiveChart from "./LiveChart";

const SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"];
const INPUT =
  "rounded border border-border bg-surface-2 px-2 py-1.5 text-sm text-fg placeholder:text-muted focus:border-accent focus:outline-none";
const money = (x: number) => x.toLocaleString("en-US", { maximumFractionDigits: 2 });

export default function PaperView() {
  const [accounts, setAccounts] = useState<PaperAccount[] | null>(null);
  const [accountId, setAccountId] = useState("");
  const [detail, setDetail] = useState<PaperAccountDetail | null>(null);
  const [orders, setOrders] = useState<PaperOrder[]>([]);
  const [prices, setPrices] = useState<Record<string, number>>({});
  const [symbol, setSymbol] = useState(SYMBOLS[0]);
  const [qty, setQty] = useState(0.01);
  const [newName, setNewName] = useState("Mi cuenta");
  const [newCash, setNewCash] = useState(10000);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    api
      .listPaperAccounts()
      .then((p) => {
        setAccounts(p.items);
        if (p.items[0]) setAccountId(p.items[0].id);
      })
      .catch((e) => setError(String(e)));
  }, []);

  const loadAccount = useCallback(async (id: string) => {
    const [d, o] = await Promise.all([api.getPaperAccount(id), api.listPaperOrders(id)]);
    setDetail(d);
    setOrders(o.items);
  }, []);

  useEffect(() => {
    if (accountId) loadAccount(accountId).catch((e) => setError(String(e)));
  }, [accountId, loadAccount]);

  // Poll live prices for the selected symbol + any held symbols.
  const symbolsKey = (detail?.positions.map((p) => p.symbol).join(",") ?? "") + "|" + symbol;
  const pricesRef = useRef(prices);
  pricesRef.current = prices;
  useEffect(() => {
    let active = true;
    const wanted = Array.from(new Set([symbol, ...(detail?.positions.map((p) => p.symbol) ?? [])]));
    const tick = async () => {
      const results = await Promise.allSettled(wanted.map((s) => api.paperPrice(s)));
      if (!active) return;
      const next = { ...pricesRef.current };
      results.forEach((r) => {
        if (r.status === "fulfilled") next[r.value.symbol] = r.value.price;
      });
      setPrices(next);
    };
    void tick();
    const h = setInterval(tick, 5000);
    return () => {
      active = false;
      clearInterval(h);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbolsKey]);

  async function createAccount() {
    setBusy(true);
    setError(null);
    try {
      const a = await api.createPaperAccount({ name: newName.trim() || "Cuenta", initial_cash: newCash });
      const p = await api.listPaperAccounts();
      setAccounts(p.items);
      setAccountId(a.id);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  async function order(side: "buy" | "sell") {
    const price = prices[symbol];
    if (!price) {
      setError("Sin precio en vivo todavía. Espera un segundo.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api.placePaperOrder(accountId, { symbol, side, qty, price });
      await loadAccount(accountId);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  if (accounts === null) return <p className="text-sm text-muted">Cargando…</p>;

  // No account yet -> creation form.
  if (accounts.length === 0) {
    return (
      <div className="mx-auto max-w-md">
        {error && <p className="mb-4 rounded border border-neg/40 bg-neg/10 p-3 text-sm text-neg">{error}</p>}
        <section className="rounded-xl border border-border bg-surface p-5">
          <h2 className="mb-1 text-sm font-semibold">Crea tu cuenta de práctica</h2>
          <p className="mb-4 text-xs text-muted">
            Dinero simulado. Opera hacia adelante con precios reales de Binance — sin broker ni riesgo.
          </p>
          <label className="block text-xs text-muted">
            nombre
            <input value={newName} onChange={(e) => setNewName(e.target.value)} className={`${INPUT} mt-1 block w-full`} />
          </label>
          <label className="mt-3 block text-xs text-muted">
            capital inicial (USDT)
            <input type="number" value={newCash} onChange={(e) => setNewCash(Number(e.target.value))} className={`${INPUT} nums mt-1 block w-full`} />
          </label>
          <button onClick={createAccount} disabled={busy} className="mt-4 rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white hover:brightness-110 disabled:opacity-50">
            Crear cuenta
          </button>
        </section>
      </div>
    );
  }

  const livePrice = prices[symbol];
  const positionsValue =
    detail?.positions.reduce((s, p) => s + p.qty * (prices[p.symbol] ?? p.avg_price), 0) ?? 0;
  const equity = (detail?.cash ?? 0) + positionsValue;

  return (
    <div className="space-y-4">
      {error && <p className="rounded border border-neg/40 bg-neg/10 p-3 text-sm text-neg">{error}</p>}

      {/* Account summary */}
      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Equity total" value={`$${money(equity)}`} />
        <Stat label="Efectivo" value={`$${money(detail?.cash ?? 0)}`} />
        <Stat label="En posiciones" value={`$${money(positionsValue)}`} />
        <Stat label="Posiciones" value={String(detail?.positions.length ?? 0)} />
      </section>

      {/* Terminal: big chart + trade panel on the right */}
      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <section className="rounded-xl border border-border bg-surface p-5">
          <h2 className="mb-3 text-sm font-semibold">{symbol} · en vivo</h2>
          <LiveChart symbol={symbol} livePrice={livePrice} height={480} />
        </section>

        <section className="rounded-xl border border-border bg-surface p-5">
          <div className="mb-4 flex items-center justify-between gap-2">
            <h2 className="text-sm font-semibold">Operar (simulado)</h2>
            <span className="text-xs text-muted">
              <span className="text-pos">●</span> en vivo
            </span>
          </div>
          <div className="space-y-3">
            <label className="block text-xs text-muted">
              símbolo
              <select value={symbol} onChange={(e) => setSymbol(e.target.value)} className={`${INPUT} mt-1 block w-full`}>
                {SYMBOLS.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </label>
            <div className="flex items-baseline justify-between text-xs text-muted">
              <span>precio</span>
              <span className="nums text-sm text-fg">{livePrice ? `$${money(livePrice)}` : "…"}</span>
            </div>
            <label className="block text-xs text-muted">
              cantidad
              <input type="number" step="0.001" value={qty} onChange={(e) => setQty(Number(e.target.value))} className={`${INPUT} nums mt-1 block w-full`} />
            </label>
            <div className="flex items-baseline justify-between text-xs text-muted">
              <span>≈ costo</span>
              <span className="nums text-sm text-fg">{livePrice ? `$${money(qty * livePrice)}` : "—"}</span>
            </div>
            <div className="grid grid-cols-2 gap-2 pt-1">
              <button onClick={() => order("buy")} disabled={busy || !livePrice} className="rounded-lg bg-pos/90 px-4 py-2.5 text-sm font-medium text-white hover:bg-pos disabled:opacity-50">
                Comprar
              </button>
              <button onClick={() => order("sell")} disabled={busy || !livePrice} className="rounded-lg bg-neg/90 px-4 py-2.5 text-sm font-medium text-white hover:bg-neg disabled:opacity-50">
                Vender
              </button>
            </div>
          </div>
        </section>
      </div>

      {/* Collapsible drawer: positions + order history */}
      <section className="rounded-xl border border-border bg-surface">
        <button
          onClick={() => setDrawerOpen((o) => !o)}
          className="flex w-full items-center justify-between gap-2 px-5 py-3 text-sm font-semibold hover:bg-surface-2/40"
        >
          <span className="flex items-center gap-2">
            <Chevron open={drawerOpen} />
            Posiciones e historial
          </span>
          <span className="rounded-full bg-surface-2 px-2 py-0.5 text-xs font-normal text-muted">
            {detail?.positions.length ?? 0} abiertas · {orders.length} órdenes
          </span>
        </button>

        {drawerOpen && (
          <div className="space-y-5 border-t border-border p-5">
            {/* Positions */}
            <div>
              <h3 className="mb-3 text-xs uppercase tracking-wide text-muted">Posiciones</h3>
              {!detail || detail.positions.length === 0 ? (
                <p className="text-sm text-muted">Sin posiciones abiertas.</p>
              ) : (
                <div className="overflow-auto rounded-lg border border-border">
                  <table className="w-full text-sm">
                    <thead className="bg-surface-2 text-[11px] uppercase tracking-wide text-muted">
                      <tr>
                        <th className="px-3 py-2 text-left font-medium">Símbolo</th>
                        <th className="px-3 py-2 text-right font-medium">Cantidad</th>
                        <th className="px-3 py-2 text-right font-medium">Precio prom.</th>
                        <th className="px-3 py-2 text-right font-medium">Actual</th>
                        <th className="px-3 py-2 text-right font-medium">Valor</th>
                        <th className="px-3 py-2 text-right font-medium">P&amp;L no real.</th>
                      </tr>
                    </thead>
                    <tbody className="nums">
                      {detail.positions.map((p) => {
                        const cur = prices[p.symbol];
                        const pnl = cur ? p.qty * (cur - p.avg_price) : null;
                        return (
                          <tr key={p.symbol} className="border-t border-border">
                            <td className="px-3 py-1.5 text-left">{p.symbol}</td>
                            <td className="px-3 py-1.5 text-right">{p.qty}</td>
                            <td className="px-3 py-1.5 text-right">${money(p.avg_price)}</td>
                            <td className="px-3 py-1.5 text-right">{cur ? `$${money(cur)}` : "…"}</td>
                            <td className="px-3 py-1.5 text-right">${money(p.qty * (cur ?? p.avg_price))}</td>
                            <td className={`px-3 py-1.5 text-right ${pnl === null ? "text-muted" : pnl >= 0 ? "text-pos" : "text-neg"}`}>
                              {pnl === null ? "—" : `${pnl >= 0 ? "+" : ""}$${money(pnl)}`}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Order history */}
            <div>
              <h3 className="mb-3 text-xs uppercase tracking-wide text-muted">Historial de órdenes</h3>
              {orders.length === 0 ? (
                <p className="text-sm text-muted">Aún no operas.</p>
              ) : (
                <div className="overflow-auto rounded-lg border border-border">
                  <table className="w-full text-sm">
                    <thead className="bg-surface-2 text-[11px] uppercase tracking-wide text-muted">
                      <tr>
                        <th className="px-3 py-2 text-left font-medium">Fecha</th>
                        <th className="px-3 py-2 text-left font-medium">Lado</th>
                        <th className="px-3 py-2 text-left font-medium">Símbolo</th>
                        <th className="px-3 py-2 text-right font-medium">Cantidad</th>
                        <th className="px-3 py-2 text-right font-medium">Precio</th>
                      </tr>
                    </thead>
                    <tbody className="nums">
                      {orders.map((o) => (
                        <tr key={o.id} className="border-t border-border">
                          <td className="px-3 py-1.5 text-left text-muted">{new Date(o.created_at).toLocaleString()}</td>
                          <td className={`px-3 py-1.5 text-left ${o.side === "buy" ? "text-pos" : "text-neg"}`}>
                            {o.side === "buy" ? "Compra" : "Venta"}
                          </td>
                          <td className="px-3 py-1.5 text-left">{o.symbol}</td>
                          <td className="px-3 py-1.5 text-right">{o.qty}</td>
                          <td className="px-3 py-1.5 text-right">${money(o.price)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </section>

      <p className="text-xs text-muted">
        Solo simulación · precios reales de Binance, órdenes ficticias · no es asesoría financiera.
      </p>
    </div>
  );
}

function Chevron({ open }: { open: boolean }) {
  return (
    <svg
      viewBox="0 0 20 20"
      className={`h-4 w-4 text-muted transition-transform ${open ? "rotate-90" : ""}`}
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M7 5l6 5-6 5" />
    </svg>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface-2/40 p-3">
      <div className="text-[11px] uppercase tracking-wide text-muted">{label}</div>
      <div className="nums mt-1 text-lg font-semibold">{value}</div>
    </div>
  );
}
