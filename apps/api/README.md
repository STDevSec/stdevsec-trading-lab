# stdevsec-api

Backend REST (FastAPI) de STDevsec Trading Lab.

## Correr local

```bash
uv sync
# Migraciones (desde apps/api, usa API_DATABASE_URL o el default de config):
cd apps/api && uv run alembic upgrade head && cd ../..
uv run uvicorn stdevsec_api.main:app --reload
```

Con Docker Compose las migraciones se aplican solas al arrancar el contenedor.

## Endpoints

Sistema:
- `GET /health`, `GET /ready` — liveness/readiness
- Docs OpenAPI en `/docs`

Dominio (`/api/v1`):
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/datasets` | Crea dataset desde JSON (valida OHLCV y persiste v1) |
| POST | `/datasets/upload` | Crea dataset desde un CSV subido (multipart) |
| GET | `/datasets` | Lista paginada |
| GET | `/datasets/{id}` | Detalle + versiones |
| POST | `/datasets/{id}/validate` | Revalida la última versión |
| GET | `/strategies` | Catálogo de estrategias built-in |
| POST | `/backtests` | Corre un backtest y persiste run + trades + equity |
| GET | `/backtests` | Lista paginada de corridas |
| GET | `/backtests/{id}` | Detalle de la corrida (incluye métricas) |
| GET | `/backtests/{id}/trades` | Round-trips (paginado) |
| GET | `/backtests/{id}/equity` | Curva de equity completa (serie ordenada) |
| GET | `/backtests/{id}/metrics` | Métricas de desempeño |

Errores con envelope único: `{"error": {"code", "message", "details"}}`.
