# ADR-0010: Indicadores técnicos en el chart (Sprint 08)

## Estado
Aceptada.

## Contexto
La UI mostraba la curva de equity de un backtest, pero no el **precio** del
instrumento ni indicadores técnicos. El backlog del usuario pide "indicadores en
el chart" (SMA, EMA, Bollinger, RSI, MACD) como paso hacia una estación de
trabajo de trading.

## Decisión
- **Cálculo en el motor** (`quant_engine.indicators`): `sma`, `ema`, `rsi`
  (Wilder), `macd`, `bollinger`. Funciones puras sobre `pandas`, con warm-up en
  NaN (nunca rellenado → sin lookahead). Se testean con pytest, y quedan
  reutilizables por estrategias futuras.
- **Endpoint** `GET /datasets/{id}/ohlcv`: devuelve las velas (`time` en segundos
  Unix para lightweight-charts) **más un bundle fijo** de indicadores con
  defaults sensatos (SMA 20/50, EMA 20, Bollinger 20/2, RSI 14, MACD 12/26/9).
  NaN → `null`. Sin parámetros por request todavía (YAGNI; se agregan cuando un
  usuario necesite afinar ventanas).
- **Frontend** `PriceChart`: candlesticks + overlays (SMA/EMA/Bollinger) sobre el
  precio, y paneles separados para **RSI** (con líneas 70/30) y **MACD** (línea +
  señal + histograma), con escalas de tiempo **sincronizadas**. Toggles por
  indicador. El front solo dibuja lo que el API ya calculó — no recomputa.

## Consecuencias
- El bundle es fijo; afinar ventanas requerirá parámetros en el endpoint (futuro).
- Tres instancias de chart (precio + RSI + MACD) sincronizadas por rango lógico;
  el scroll sobre el chart hace zoom (comportamiento estándar de charts de trading).
- La serie se devuelve completa (acotada por `max_candles`), consistente con la
  curva de equity.
