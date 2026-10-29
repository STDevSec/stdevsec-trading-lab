# Threat Model (STRIDE-lite) — Sprint 01

Alcance actual: importación/validación de datasets OHLCV, generación sintética,
y endpoints `/health` y `/ready` de la API. Sin autenticación ni persistencia
todavía; sin trading real ni señales.

## Activos
- Integridad y reproducibilidad de los datos de mercado.
- Disponibilidad del proceso de la API.
- (Futuro) aislamiento entre tenants y datos de usuario.

## Entradas no confiables
- Archivos de dataset (CSV) subidos o provistos por el usuario.
- Parámetros de requests a la API.

## Amenazas y mitigaciones

| STRIDE | Amenaza | Mitigación (Sprint 01) |
|--------|---------|------------------------|
| Tampering | CSV con fórmulas (`=,+,-,@`) que ejecutan en una hoja de cálculo al exportar | `neutralize_csv_value` antepone `'` al exportar (`market-data`) |
| Elevation / RCE | Ejecución de código vía archivos subidos o deserialización | Solo se parsean formatos de datos; **nunca `pickle`** con datos externos; no se ejecuta código del usuario |
| Tampering | Path traversal con rutas provistas por el usuario | `safe_resolve` confina rutas bajo un base dir; se rechazan `..` y rutas absolutas |
| DoS | Archivos enormes agotan memoria | Cap de tamaño (`MAX_UPLOAD_BYTES`, 50 MiB) **antes** de parsear |
| Tampering | Datos inválidos corrompen resultados silenciosamente | El validador **reporta, no repara**; `is_valid=False` bloquea el uso aguas arriba |
| Info disclosure | Secretos en el repo o logs | `.env` fuera de git; `.env.example` sin valores reales; scan de deps en CI |
| Info disclosure | Servicios internos expuestos | Postgres/Redis no publicados por defecto en Compose |
| Spoofing/Repudiation | (Futuro) sin auth ni correlación | Request-ID por petición ya presente; auth llega en sprint posterior |

## Riesgos residuales (Sprint 01)
- Sin autenticación ni rate limiting todavía: la API no debe exponerse pública
  en este estado (solo local / detrás de proxy en dev).
- Validación de contenido de CSV cubre calidad OHLCV, no malware embebido en
  nombres/campos arbitrarios fuera del esquema esperado.

Estos riesgos se cierran en sprints de API/auth/persistencia y se re-evalúan ahí.
