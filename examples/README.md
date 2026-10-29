# Examples

Ejemplos reproducibles. Los datasets se generan con semilla fija, no se versionan
crudos (ver `.gitignore`); se regeneran con:

```bash
uv run python -m quant_engine.synthetic --rows 500 --seed 42 --out examples/sample_ohlcv.csv
```

El dataset que consume el chart del frontend se genera con:

```bash
uv run python scripts/gen_sample.py   # -> apps/web/public/sample-ohlcv.json
```
