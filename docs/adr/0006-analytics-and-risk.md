# ADR-0006: Métricas de desempeño y gestión de riesgo (MVP)

- Estado: Aceptado
- Fecha: 2026-10-29

## Contexto

Tras el motor de backtesting (ADR-0005) se necesitan métricas de desempeño y
controles de riesgo. El spec exige que cada métrica documente fórmula, supuestos
y limitaciones, y que no se fabriquen resultados.

## Decisión

### Analytics (`quant_engine.analytics`)
Se calculan sobre `BacktestResult` (equity curve + round-trips con P&L realizado):

- **win rate** = trades ganadores / total.
- **profit factor** = ganancia bruta / pérdida bruta (|·|); `inf` si no hay
  pérdidas, `None` si no hay trades.
- **expectancy** = P&L medio por trade.
- **avg win / avg loss** = P&L medio de ganadores / perdedores.
- **net profit / total return** sobre el capital inicial.
- **max drawdown** = mayor caída pico-a-valle del equity (fracción ≥ 0).
- **Sharpe** = `mean(r)/std(r)·√(periodos_por_año)`, risk-free = 0, con `r`
  retornos por barra; `None` si < 2 retornos o volatilidad cero. **Limitación:**
  asume retornos ~i.i.d., que las estrategias reales violan → indicativo, no
  garantía.
- **rachas** consecutivas de ganancias/pérdidas; **retornos mensuales**.

Métricas indefinidas devuelven `None`, nunca un número engañoso.

### Risk (`quant_engine.risk` + backtester)
- **position_size_from_risk**: `units = capital · riesgo / |entry − stop|`.
- **risk_reward_ratio**: `|target − entry| / |entry − stop|`.
- **max_drawdown_halt** (en `run_backtest`): al caer esa fracción desde el pico,
  liquida y queda flat el resto de la corrida (determinista, sin recuperación
  automática).

## Consecuencias
- (+) Métricas y riesgo testeados con casos calculados a mano.
- (−) MVP de un activo long/flat: límites de pérdida diaria, exposición
  multi-instrumento y máximo de posiciones simultáneas quedan **fuera de alcance**
  hasta el motor multi-activo/intradía (ADR futuro).
