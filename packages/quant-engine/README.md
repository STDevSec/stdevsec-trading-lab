# quant-engine

Motor cuantitativo **determinista** e independiente (no importa FastAPI, Postgres
ni frontend). Usable como paquete Python standalone.

Sprint 01:
- `quant_engine.validation.validate_ohlcv(df)` → reporte estructurado de calidad
  de datos OHLCV. **Nunca repara en silencio**: solo reporta.
- `quant_engine.synthetic.generate_ohlcv(...)` → datasets OHLCV sintéticos
  reproducibles (semilla fija), siempre válidos según el validador.

```bash
uv run python -m quant_engine.synthetic --rows 500 --seed 42 --out examples/sample_ohlcv.csv
```
