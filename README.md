# STDevsec Trading Lab

Plataforma **open-source** de investigación cuantitativa, aprendizaje de trading,
backtesting y análisis estadístico. **Solo simulación** — sin dinero real, sin
señales automáticas, sin garantías de rentabilidad.

> ⚠️ Este software es educativo y de investigación. No es asesoría financiera.
> Los resultados simulados **no** representan desempeño real de mercado.

## Qué es

Un entorno para aprender mercados, importar y validar datos históricos (OHLCV),
desarrollar estrategias, hacer **backtesting determinista y reproducible**,
analizar riesgo/desempeño y llevar un diario de trading.

El **motor cuantitativo** (`packages/quant-engine`) es independiente de la API,
la base de datos y el frontend: se puede usar como paquete Python standalone.

## Arquitectura (resumen)

```
Frontend (Next.js) → REST API (FastAPI) → Servicios → Dominio
                                              → Quant Engine (standalone)
                                              → Persistencia (PostgreSQL, Redis, Parquet)
```

Monolito modular con fronteras de dominio claras. Sin microservicios salvo
justificación real. Ver `docs/architecture/` y los ADR en `docs/adr/`.

## Estructura del monorepo

| Ruta | Qué contiene |
|------|--------------|
| `apps/web` | Frontend Next.js + Lightweight Charts |
| `apps/api` | Backend FastAPI (health/ready en Sprint 01) |
| `packages/quant-engine` | Validación OHLCV + generación sintética determinista |
| `packages/market-data` | Importación/IO de datos de mercado (CSV→Parquet) |
| `packages/shared-contracts` | Tipos/esquemas TypeScript compartidos (Zod) |
| `docs/` | Arquitectura, ADR, seguridad, API, trading, tutoriales |
| `infrastructure/` | Docker y Compose |

## Requisitos

- **Python 3.12** (fijado; ver ADR-0003) gestionado con [uv](https://docs.astral.sh/uv/)
- **Node 20+** y npm
- **Docker + Docker Compose** (para el stack completo)

## Desarrollo local

```bash
# Python: instala toolchain y deps del workspace (pinnea Python 3.12)
uv python install 3.12
uv sync

# Calidad
uv run ruff check .
uv run mypy
uv run pytest

# Genera un dataset sintético reproducible (semilla fija)
uv run python -m quant_engine.synthetic --out examples/sample_ohlcv.csv

# API
uv run uvicorn stdevsec_api.main:app --reload   # http://127.0.0.1:8000/health

# Frontend
cd apps/web && npm install && npm run dev        # http://localhost:3000

# Stack completo
cp .env.example .env
docker compose up --build
```

## Seguridad

Los datasets subidos y toda entrada de usuario se tratan como **no confiables**.
No se ejecuta código subido, no se usa `pickle` con datos externos, los servicios
internos (Postgres/Redis) no se exponen por defecto. Ver `SECURITY.md` y
`docs/security/threat-model.md`.

## Licencia

Apache License 2.0 — ver `LICENSE` y `NOTICE`.
