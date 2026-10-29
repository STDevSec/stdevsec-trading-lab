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

## Métricas (futuro)

Cada métrica (win rate, profit factor, expectancy, max drawdown, Sharpe cuando
sea estadísticamente apropiado, etc.) documentará su fórmula, supuestos y
limitaciones antes de usarse.
