# Trading — conceptos y supuestos

Documentación de los supuestos cuantitativos de la plataforma. **Educativo, solo
simulación.** Nada aquí es asesoría financiera ni garantiza rentabilidad.

## Modelo de ejecución (futuro backtesting)

- Backtesting **event-driven**, determinista, **sin lookahead**.
- Una señal calculada con el **cierre** de una vela **no** ejecuta en ese mismo
  cierre: por defecto ejecuta en la **apertura de la siguiente** vela, salvo que
  un modelo de ejecución justificado explícitamente lo permita.
- Costos de transacción explícitos, slippage configurable, calendarios de mercado.

## Datos

Formato OHLCV: `timestamp` (UTC, tz-aware), `open`, `high`, `low`, `close`,
`volume`. Reglas de validez: ver `quant_engine.validation`. Los datos inválidos
**no se reparan en silencio**.

## Métricas y riesgo

`quant_engine.analytics.compute_metrics(result)` calcula sobre un backtest:
win rate, profit factor, expectancy, net profit, total return, max drawdown,
avg win/avg loss, Sharpe (anualizado, risk-free 0), rachas consecutivas y
retornos mensuales. Cada fórmula, supuesto y limitación está en
[ADR-0006](../adr/0006-analytics-and-risk.md); las métricas indefinidas devuelven
`None`, nunca un número engañoso.

Riesgo: `position_size_from_risk` (sizing por riesgo por trade),
`risk_reward_ratio`, y `run_backtest(max_drawdown_halt=...)` que liquida y queda
flat al superar un drawdown. Límites diarios y multi-activo: pendientes (ADR-0006).
