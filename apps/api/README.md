# stdevsec-api

Backend REST (FastAPI) de STDevsec Trading Lab.

Sprint 01: endpoints de liveness/readiness.

```bash
uv run uvicorn stdevsec_api.main:app --reload
# GET http://127.0.0.1:8000/health   -> {"status":"ok"}
# GET http://127.0.0.1:8000/ready    -> {"status":"ready", ...}
# Docs OpenAPI en /docs
```
