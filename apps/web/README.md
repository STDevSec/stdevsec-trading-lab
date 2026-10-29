# @stdevsec/web

Frontend (Next.js 14 + Lightweight Charts) de STDevsec Trading Lab.

## Correr local

```bash
npm install
# Apunta al API local (default si no se define):
export NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev --workspace @stdevsec/web
```

Requiere el API corriendo (`apps/api`) con su base de datos migrada.

## Flujo de dominio

La home (`app/page.tsx`) monta `TradingLab`:

1. **Dataset** — lista los datasets del API; botón *Generar dataset de ejemplo*
   crea uno sintético (GBM determinista, en el navegador) vía `POST /datasets`.
2. **Estrategia** — catálogo desde `GET /strategies`; los parámetros se renderizan
   dinámicamente según el catálogo.
3. **Backtest** — `POST /backtests`; muestra métricas + curva de equity
   (`GET /backtests/{id}/equity`).

Todas las respuestas del API se validan con Zod (`lib/api.ts`) — el backend se
trata como input no confiable, igual que el archivo de datos sintéticos.
