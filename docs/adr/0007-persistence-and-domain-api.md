# ADR-0007: Persistencia (SQLAlchemy/Alembic) y API de dominio (MVP)

- Estado: Aceptado
- Fecha: 2026-10-29

## Contexto

Hay que persistir datasets y resultados de backtest y exponerlos por REST, sin
acoplar el `quant-engine` (ADR-0002) a la base de datos.

## Decisión

- **SQLAlchemy 2.x** (modelos tipados `Mapped`) + **Alembic** para migraciones.
  **Postgres** en producción; **SQLite in-memory** en los tests (tipos
  cross-dialect: `String`/`JSON`/`Float`). La API crea el esquema con
  `alembic upgrade head`, no con `create_all` en producción.
- **Modelos del slice de backtest:** `Dataset`, `DatasetVersion`, `BacktestRun`,
  `BacktestTrade`, `EquitySnapshot`. Los candles OHLCV se guardan como **JSON**
  en `DatasetVersion.candles` (datasets educativos acotados por `max_candles`);
  Parquet/object-storage quedan **diferidos**.
- **Endpoints `/api/v1`:** `datasets` (crear→valida y persiste, listar, ver,
  revalidar), `strategies` (catálogo de built-ins), `backtests` (correr→persiste
  run+trades+equity, ver, trades, métricas). Paginación `limit/offset` y
  **envelope de error único** `{"error":{code,message,details}}`.
- La capa de servicios orquesta: convierte candles↔DataFrame, llama al
  `quant-engine` (validación, backtest, métricas) y persiste. El motor sigue sin
  conocer la BD.

## Diferido (con razón)
- **User/Workspace/WorkspaceMember** y auth/multi-tenant → sprint de auth; por
  eso no hay aún aislamiento por tenant ni autorización (la API no debe exponerse
  pública en este estado).
- **Instrument**, **Strategy/StrategyVersion** (las estrategias se referencian por
  nombre+params inline), **TradingJournalEntry**, **LearningProgress**,
  **AuditEvent** → sus sprints respectivos.
- Carga de CSV por multipart (hoy se aceptan candles JSON, mismo camino de
  validación).

## Consecuencias
- (+) Flujo completo dataset→backtest→métricas persistido y testeado end-to-end.
- (−) Candles en JSON no escalan a datasets enormes; se migrará a Parquet cuando
  haga falta. Sin auth todavía: uso local/self-hosted detrás de proxy.
