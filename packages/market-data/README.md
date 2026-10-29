# market-data

IO de datos de mercado para STDevsec Trading Lab. Trata todo archivo como **no
confiable**:

- `read_ohlcv_csv(path, max_bytes=...)` — importa CSV OHLCV con **límite de
  tamaño** y timestamps normalizados a UTC tz-aware. No ejecuta nada, no usa
  `pickle`, no repara datos (eso lo reporta `quant_engine.validate_ohlcv`).
- `safe_resolve(base, user_path)` — resuelve rutas confinadas a `base`
  (**anti path-traversal**).
- `write_ohlcv_csv(df, path)` — exporta neutralizando **CSV injection**
  (`= + - @` al inicio de celda de texto).
