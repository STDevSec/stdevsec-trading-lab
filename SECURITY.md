# Política de Seguridad

## Reportar una vulnerabilidad

Reporta de forma responsable y privada a **st.devsec@gmail.com**. No abras un
issue público para vulnerabilidades. Incluye pasos de reproducción y el impacto
esperado. Respondemos en cuanto sea posible y acordamos una divulgación
coordinada.

## Modelo de seguridad (resumen)

El proyecto sigue OWASP ASVS y OWASP API Security Top 10 como guía. El threat
model vive en [`docs/security/threat-model.md`](docs/security/threat-model.md).

### Supuestos
- Toda entrada de usuario y **todo dataset subido es no confiable**.
- El motor cuantitativo no ejecuta código proporcionado por el usuario.

### Controles por defecto
- **CSV injection:** campos que empiezan con `= + - @` se neutralizan al exportar.
- **Path traversal:** rutas de archivos validadas y confinadas; sin rutas del cliente.
- **Deserialización:** prohibido `pickle` con datos externos; solo formatos de datos (CSV/Parquet) parseados sin ejecución.
- **Límites:** tamaño máximo de upload y de dataset acotados (`MAX_UPLOAD_BYTES`).
- **Servicios internos:** PostgreSQL y Redis no se exponen públicamente por defecto.
- **Secretos:** fuera del repositorio (`.env`, ignorado). Escaneo de dependencias en CI.
- **Multi-tenant (futuro):** aislamiento por tenant en app y persistencia; nunca
  se confía en identificadores de tenant del cliente sin autorización.

### Riesgos residuales
Se documentan por sprint en el threat model. El MVP no hace trading real ni
genera señales, lo que reduce la superficie de abuso financiero.

## Alcance
Solo simulación. No hay ejecución de órdenes con dinero real en el MVP.
