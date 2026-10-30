# ADR-0012: Paper trading (Sprint 10)

## Estado
Aceptada.

## Contexto
Último ítem del backlog del usuario: **operar hacia adelante** en simulado con
precios reales, para practicar sin riesgo. A diferencia del backtesting (pasado,
de un jalón), el paper trading avanza en tiempo real.

## Decisión
- **Precio en vivo desde Binance** (`GET /api/v1/paper/price?symbol=`): endpoint
  público de Binance, **sin API key**, vía `urllib` a un host fijo. El símbolo se
  valida con regex antes de construir la URL. Fallos de red → `UpstreamError`
  (502). Elegido por ser gratis, sin registro y con buena cobertura de cripto.
- **El fill usa el precio que envía el cliente** (el precio en vivo que observó),
  no uno que el backend re-consulta. Mantiene el servicio **puro y testeable**
  (sin red en los tests) y es honesto para una simulación. `ponytail:` si se
  quisiera fill server-side, el endpoint de precio ya existe para consultarlo.
- **Long-only, sin apalancamiento**: una venta no puede exceder lo que se tiene.
  Compra valida fondos; venta valida posición. P&L realizado se refleja en el
  efectivo; el no realizado lo calcula el frontend con el precio en vivo.
- **Modelos** `PaperAccount` (efectivo) / `PaperPosition` (neta por símbolo) /
  `PaperOrder` (histórico). Migración Alembic.
- **Frontend**: vista *Paper trading* (sale de "pronto", cierra el backlog).
  Precio en vivo (poll cada 5 s), panel de compra/venta, posiciones con valor y
  P&L no realizado, equity total e historial.

## Consecuencias
- Depende de que Binance sea alcanzable desde el backend; si no, el precio falla
  (502) y no se puede operar, pero el resto del lab sigue.
- Sin shorting/leverage ni tipos de orden avanzados (market only). Ampliable.
- Sigue siendo **100% simulación**: ningún endpoint toca un broker ni mueve
  dinero real. El disclaimer se mantiene.
