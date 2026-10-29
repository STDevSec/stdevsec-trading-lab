# ADR-0009: Carga de datasets por CSV (Sprint 06)

## Estado
Aceptada.

## Contexto
Hasta el Sprint 05 un dataset solo podía crearse enviando candles en JSON o
generando datos sintéticos. Para "elegir un instrumento real" (AAPL, BTC…) el
usuario necesita subir sus propios precios. El paquete `market-data` ya tenía un
lector de CSV seguro (cap de tamaño, path traversal, inyección de fórmulas), pero
solo desde disco y sin exponerse por la API.

## Decisión
- **Lector desde bytes** en `market-data`: `read_ohlcv_csv_bytes`, para parsear un
  upload que nunca toca disco, con el mismo cap de tamaño **antes** de parsear. La
  normalización de timestamps se extrajo a un helper compartido con el lector de
  disco (sin duplicar lógica).
- **Reúso total del camino de persistencia**: el CSV parseado se convierte a
  `CandleIn` (`candles_from_df`) y se pasa por **el mismo** `create_dataset` que el
  alta JSON. Así el upload obtiene idénticas garantías: validación OHLCV del motor
  (reporta, no repara), versionado y almacenamiento. Si el CSV falla validación,
  se rechaza con el envelope de error, nombrando la fila/columna problemática.
- **Endpoint** `POST /api/v1/datasets/upload` (multipart): `file` + `name`,
  `timeframe`, `symbol?`. Requiere `python-multipart`.
- **Límites explícitos** (agotamiento de recursos): `max_upload_bytes` (bytes, antes
  de parsear → `413 payload_too_large`) y `max_candles` (filas, → `422`).
- **Frontend**: caja de carga en la sección Dataset (símbolo, timeframe, archivo),
  más "descargar CSV de ejemplo" generado en el navegador para que el usuario tenga
  el formato exacto. Tras subir, el dataset queda seleccionado y listo para backtest.

## Consecuencias
- El CSV sube **en memoria**; el cap de bytes acota el uso antes de parsear. Para
  archivos muy grandes en el futuro se puede pasar a streaming/parquet.
- No se conecta ningún proveedor de datos todavía: el usuario trae su propio CSV.
  La conexión a un feed (p. ej. Binance) queda para el sprint de paper trading.
- El formato de CSV es fijo (`timestamp,open,high,low,close,volume`, timestamp
  ISO-8601 UTC). Mapear otros formatos (p. ej. Yahoo) sería un adaptador aparte.
