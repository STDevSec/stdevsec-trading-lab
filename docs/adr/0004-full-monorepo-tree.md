# ADR-0004: Crear el árbol completo del monorepo en Sprint 01

- Estado: Aceptado
- Fecha: 2026-10-29

## Contexto

Se consideró diferir los paquetes `market-data` y `shared-contracts` hasta que un
sprint los necesitara (YAGNI), creando solo lo que tiene uso inmediato.

## Decisión

El dueño del producto decidió **crear el árbol completo del spec desde Sprint 01**,
incluyendo `packages/market-data` y `packages/shared-contracts`, aun cuando su
alcance en este sprint es mínimo.

En Sprint 01 estos paquetes **sí tienen contenido real y probado** (no son
cascarones): `market-data` implementa IO seguro de CSV y `shared-contracts`
define los esquemas Zod/tipos que el frontend ya consume.

## Consecuencias

- (+) Estructura estable desde el inicio; menos refactor de rutas luego.
- (+) Convención clara de dónde vive cada cosa para colaboradores.
- (−) Un poco más de superficie que mantener desde el día uno; se mitiga con tests
  y manteniendo cada paquete pequeño hasta que crezca su necesidad.
