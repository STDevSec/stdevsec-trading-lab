# ADR-0008: Frontend de dominio (Sprint 05)

## Estado
Aceptada.

## Contexto
Los Sprints 01–04 dejaron el motor cuantitativo y una API de dominio
(`/api/v1`: datasets, strategies, backtests) con persistencia. El frontend solo
mostraba un chart de datos sintéticos estáticos. Falta una UI que recorra el
flujo real: elegir/crear un dataset → lanzar un backtest → ver equity + métricas.

## Decisión
- **Cliente tipado con validación en el borde** (`apps/web/lib/api.ts`): cada
  respuesta se valida con Zod antes de usarse. El backend se trata como input no
  confiable, igual que ya se hacía con el archivo de datos sintéticos.
- **Base URL por entorno**: `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).
- **Un orquestador cliente** (`TradingLab.tsx`) con tres secciones (dataset,
  estrategia, resultados) en lugar de múltiples páginas/rutas — el flujo es lineal
  y no amerita routing aún.
- **Parámetros de estrategia dinámicos**: se renderizan desde el catálogo del API
  (`GET /strategies`), no hardcodeados en el front.
- **Seeding desde el navegador**: botón que genera un dataset sintético (GBM
  determinista en JS) y lo crea vía `POST /datasets`, para que la UI sea usable
  sin correr el seeder de CLI. No es el modelo del motor; solo velas suficientes
  para correr un backtest.
- **Nuevo endpoint** `GET /backtests/{id}/equity`: los snapshots de equity ya se
  persistían pero no se exponían. Se devuelve la serie completa (no paginada)
  porque un chart necesita la curva entera; acotada por `max_candles`.

## Consecuencias
- La UI depende del API corriendo y migrado; sin él muestra el error del envelope.
- Carga de CSV / upload de archivos queda pendiente (se agrega cuando se necesite);
  por ahora el seeding sintético y la creación vía API cubren el flujo.
- El GBM del navegador duplica *conceptualmente* el del motor, pero es trivial y
  solo para demo; no se comparte código para no acoplar front y engine.
