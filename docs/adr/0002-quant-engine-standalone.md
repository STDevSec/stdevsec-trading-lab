# ADR-0002: El quant-engine es independiente y standalone

- Estado: Aceptado
- Fecha: 2026-10-29

## Contexto

El motor cuantitativo (validación, generación, y a futuro estrategias,
backtesting y métricas) es el núcleo científico. Si se acopla a FastAPI o a la
base de datos, deja de ser reproducible y testeable de forma aislada.

## Decisión

`packages/quant-engine` **no importa** FastAPI, SQLAlchemy, Redis ni el frontend.
Recibe y devuelve estructuras de datos puras (DataFrames, dataclasses). Se puede
instalar y usar como paquete Python independiente, y correr en un notebook.

## Consecuencias

- (+) Reproducibilidad y tests deterministas sin levantar la API ni la BD.
- (+) Reusable fuera de la plataforma (investigación, CI, ejemplos).
- (−) La API debe adaptar entre sus modelos (Pydantic) y las estructuras del
  motor; es un costo aceptable y se concentra en la capa de servicios.
- Un test de frontera verifica que el motor no importe dependencias de la app.
