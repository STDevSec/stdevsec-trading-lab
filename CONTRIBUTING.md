# Contribuir a STDevsec Trading Lab

¡Gracias por tu interés! Este proyecto es educativo y open-source (Apache-2.0).

## Principios no negociables

- **Reproducibilidad primero.** Nada de resultados inventados. Semillas fijas en
  datos sintéticos; datasets golden con resultados esperados.
- **Sin lookahead.** Una señal en el cierre de una vela no ejecuta en ese mismo
  cierre (ver ADR de ejecución).
- **Sin dinero real / sin señales** en el MVP.
- **Seguridad por defecto.** Entrada de usuario = no confiable. Nada de ejecutar
  código subido ni `pickle` con datos externos. Nunca commitees secretos.

## Flujo

1. Abre un issue describiendo el cambio.
2. Rama desde `main`: `feat/...`, `fix/...`, `docs/...`.
3. Cambios pequeños y revisables. Preserva funcionalidad existente.
4. Añade **tests** y actualiza **documentación**.
5. Corre la calidad local antes de abrir PR.

## Calidad local

```bash
uv sync
uv run ruff check .      # lint + seguridad (bandit)
uv run mypy              # tipos estrictos
uv run pytest            # tests
cd apps/web && npm run lint && npm run build
```

Cada feature entra con: código, tests, documentación, manejo de errores,
criterios de aceptación y consideraciones de seguridad.

## Commits

Convención [Conventional Commits](https://www.conventionalcommits.org/):
`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`.

## Decisiones de arquitectura

Cualquier cambio arquitectónico se documenta con un **ADR** en `docs/adr/`
(copia el formato de los existentes). No cambies el alcance del producto sin ADR.
