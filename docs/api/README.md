# API

Contratos REST versionados (`/api/v1/...`). La documentación OpenAPI se sirve en
`/docs` cuando la API corre.

Sprint 01 expone solo endpoints de sistema:

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Liveness: el proceso está arriba |
| GET | `/ready` | Readiness: dependencias alcanzables |

Los contratos de dominio (datasets, strategies, backtests) se añadirán en sprints
posteriores y se reflejarán aquí y en `packages/shared-contracts`.
