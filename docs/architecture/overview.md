# Arquitectura — visión general

STDevsec Trading Lab es un **monolito modular** con fronteras de dominio claras.
No usamos microservicios salvo que una necesidad real de escala/aislamiento lo
justifique (ver [ADR-0001](../adr/0001-modular-monolith.md)).

## Capas

```
┌─────────────────────────────────────────────┐
│ Frontend  (apps/web, Next.js + Lightweight Charts)
└───────────────┬─────────────────────────────┘
                │ HTTP/REST (contratos en packages/shared-contracts)
┌───────────────▼─────────────────────────────┐
│ REST API  (apps/api, FastAPI)                │
│   → Servicios de aplicación                  │
│   → Capa de dominio                          │
└───────────────┬─────────────────────────────┘
                │ llamadas Python directas
┌───────────────▼─────────────────────────────┐
│ Quant Engine  (packages/quant-engine)        │  ← independiente, standalone
│   validación OHLCV · generación sintética    │
│   (futuro: estrategias, backtesting, métricas)│
├──────────────────────────────────────────────┤
│ Market Data  (packages/market-data)          │  IO seguro CSV/Parquet
├──────────────────────────────────────────────┤
│ Persistencia  PostgreSQL · Redis · Parquet   │  (futuros sprints)
└──────────────────────────────────────────────┘
```

## Reglas de dependencia

- **El quant-engine no importa** FastAPI, SQLAlchemy ni nada de la web. Es un
  paquete Python usable solo (ver [ADR-0002](../adr/0002-quant-engine-standalone.md)).
  Un test de frontera lo verifica.
- `market-data` puede depender de `quant-engine` (para validar), no al revés.
- La API orquesta; la lógica cuantitativa vive en los paquetes.
- El frontend solo habla con la API; comparte tipos vía `shared-contracts`.

## Determinismo y reproducibilidad

- Datos sintéticos con **semilla fija**.
- Backtesting (futuro) **event-driven, sin lookahead**: una señal en el cierre de
  una vela ejecuta por defecto en la **apertura de la siguiente** vela.
- Versionado de datasets y de estrategias; identificadores de experimento.

## Estado por sprint

Sprint 01 implementa: validación OHLCV, generador sintético, IO de market-data,
skeleton de API (`/health`, `/ready`), chart en el frontend, CI. El resto de
módulos (estrategias, backtesting, riesgo, journal, analytics, comunidad) son
sprints posteriores.
