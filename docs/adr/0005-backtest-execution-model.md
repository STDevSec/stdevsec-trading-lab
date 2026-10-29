# ADR-0005: Modelo de ejecución del backtester (señal en cierre → fill en apertura siguiente)

- Estado: Aceptado
- Fecha: 2026-10-29

## Contexto

El spec exige backtesting **determinista y sin lookahead**: una señal calculada
con el cierre de una vela no debe ejecutarse en ese mismo cierre.

## Decisión

El motor (`quant_engine.backtest`) es **event-driven, long/flat, de un activo**:

- La estrategia produce un **peso objetivo** en `[0,1]` por barra. El peso de la
  barra `t` se decide con información hasta el **cierre de `t`**.
- El peso decidido en el cierre de `t-1` se **ejecuta en la apertura de `t`**.
  Así, ninguna señal ejecuta en la misma barra que la generó.
- La barra 0 no tiene señal previa ⇒ se entra flat; la primera entrada posible es
  en la apertura de la barra 1.
- El equity se marca a mercado en cada **cierre**.
- Costos explícitos: `commission_bps` sobre el nocional operado y `slippage_bps`
  moviendo el fill en contra (compras llenan más caro, ventas más barato).

## Consecuencias

- (+) Sin lookahead por construcción; un test verifica que cambiar la señal de la
  última barra no altera resultados.
- (+) Determinista y reproducible; golden tests calculados a mano.
- (−) Modelo de llenado simple (apertura siguiente, sin parcial ni order book).
  Modelos más realistas (limit orders, fills parciales, calendarios de sesión)
  se añadirán cuando se justifiquen, documentados en nuevos ADR.
- Alcance Sprint 02: long/flat, un activo. Sizing fraccional, short y múltiples
  posiciones son sprints posteriores (Módulo E — Risk).
