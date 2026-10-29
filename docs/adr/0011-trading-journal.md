# ADR-0011: Diario de trading (Sprint 09)

## Estado
Aceptada.

## Contexto
El backlog del usuario pide una **bitácora de trader**: registrar ideas y
operaciones con notas, etiquetas y **capturas de pantalla**, para revisarlas
después. No existía ninguna entidad de diario (estaba listada como diferida en
ADR-0007).

## Decisión
- **Modelos** `JournalEntry` (título, notas, tags JSON, `run_id` opcional,
  `created_at`) y `JournalImage` (captura). `run_id` es FK **SET NULL**: una nota
  puede referenciar un backtest, pero sobrevive si esa corrida se borra.
- **Capturas como BLOB en la DB** (`LargeBinary`), no en el filesystem: funciona
  igual en SQLite (dev) y Postgres (prod) sin montar volúmenes ni configurar
  almacenamiento de objetos. Cada imagen se acota con `max_upload_bytes` y se
  rechaza si no es `image/*`. `ponytail:` si el diario crece, mover a object
  storage; el blob tiene techo conocido.
- **Endpoints** bajo `/journal`: CRUD de entradas + `POST …/images` (multipart) y
  `GET …/images/{id}` que sirve los bytes con su `content-type`.
- **Frontend**: se habilita la vista *Diario* en el sidebar (sale de "pronto").
  Formulario (título, notas, etiquetas, captura) + lista de entradas con chips de
  tags y miniaturas. Borrado con confirmación inline (sin diálogos del navegador).

## Consecuencias
- La lista no trae las imágenes (solo metadatos en el detalle); el front hace
  N+1 para miniaturas. `ponytail:` aceptable para un diario personal; agregar
  imágenes a la lista si crece.
- Las capturas viven en la DB → los respaldos de la DB ya las incluyen, pero la
  DB pesa más. El cap por imagen y el tipo validado limitan el riesgo.
- El `DELETE` de entrada cascada a sus imágenes (FK CASCADE).
