# Compose

El stack de desarrollo vive en `docker-compose.yml` en la raíz del repo.

```bash
cp .env.example .env
docker compose up --build
```

Servicios: `postgres`, `redis`, `api` (FastAPI, :8000), `web` (Next.js, :3000).
Postgres y Redis se atan a `127.0.0.1` — no se exponen públicamente.

Overrides por entorno (producción, staging) se agregarán aquí como
`docker-compose.<env>.yml` cuando se necesiten.
