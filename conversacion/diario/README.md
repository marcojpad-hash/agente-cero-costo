# Diario compartido

Directorio de eventos JSONL append-only, particionado por mes UTC.

Formato de archivo: `YYYY-MM/YYYY-MM-DD.jsonl`.

Cada línea es un objeto JSON con `timestamp`, `source_agent`, `source_channel`, `event_type`, `content`, `artifact_refs`, `project_ids`, `sensitivity` y `correlation_id`.

No se inventan turnos ni se reconstruyen conversaciones no disponibles. Cada conector debe publicar los mensajes que realmente pueda leer. Las entradas deben incluir origen y nivel de fidelidad (verbatim, summary o metadata).
