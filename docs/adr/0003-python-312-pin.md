# ADR-0003: Fijar Python 3.12 con uv

- Estado: Aceptado
- Fecha: 2026-10-29

## Contexto

El spec pide "Python 3.12+". La máquina de desarrollo trae Python 3.14, pero
varias dependencias cuantitativas (pandas, numpy, pyarrow) pueden no tener wheels
estables para versiones muy nuevas, lo que rompería la reproducibilidad y
obligaría a compilar.

## Decisión

Fijamos **Python 3.12** vía `uv` (`.python-version` = 3.12, `requires-python
>=3.12,<3.13`). `uv` gestiona el intérprete, el entorno y el lockfile en una sola
herramienta.

## Consecuencias

- (+) Wheels disponibles y estables para el stack cuantitativo; builds reproducibles.
- (+) Lockfile (`uv.lock`) garantiza las mismas versiones en dev y CI.
- (−) No usamos features de 3.13/3.14 por ahora; se revisará cuando el ecosistema
  publique wheels estables.
