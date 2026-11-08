# Actualizaciones

Registro cronológico de indicaciones y cambios de información. Solo se
agrega, nunca se borra. Cada línea es un aviso que reciben los otros
modelos aunque no estén en la interacción directa.

- 2026-11-08 04:47 (v1) — Se crea el sistema de avisos: cada indicación o cambio de información genera un aviso con versión, y la sanguijuela lo adjunta automáticamente a cada encargo. Lección que lo motiva: la sanguijuela respondió genérica porque el encargo no llevaba el contexto; desde ahora el contexto viaja solo.
- 2026-11-08 04:45 (v2) — La sanguijuela ya adjunta sola el contexto vigente (versión + últimas actualizaciones) a cada encargo; el puente de lectura acepta --contexto. Lección: el encargo debe llevar el contexto adentro.
- 2026-11-08 04:48 (v3) — Se creó el conector macho-hembra: emitir.py anuncia y recibir.py recibe, y viceversa.
- 2026-11-08 04:57 (v4) — El foquito está en la URL pública del estado: cualquier modelo con navegación lo lee.
- 2026-11-08 05:17 (v5) — PR #2 integrado (merge 8cd83be1) y emisión real probada: el Issue #4 se convirtió en gh-issue-4.json en el bus. El túnel de Issues está vivo.
