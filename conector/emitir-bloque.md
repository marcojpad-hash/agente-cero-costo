# Bloque [EMITIR]

El lado emisor para los modelos que viven en su propia app (ChatGPT,
Grok, Gemini): no tienen el repo ni los scripts, pero todos pueden
escribir texto. Cuando tengan información nueva para el equipo, la
emiten con este bloque. El usuario pega la respuesta aquí y
`aplicar.py` la escribe en el bus.

## El formato

```
[EMITIR]
de: <nombre del modelo>
tipo: actualizacion
mensaje: <lo nuevo, en una línea>
[/EMITIR]
```

- `de`: el nombre del modelo que emite (p. ej. ChatGPT, Grok, Gemini).
- `tipo`: `actualizacion`, `indicacion`, `aviso` o `hecho`.
- `mensaje`: lo nuevo, en una línea. Sin el bloque no se aplica nada.

## La instrucción para pegar en el otro modelo

Pégale esto una vez al modelo con el que hables:

```
Antes de responder, lee el estado vigente aquí:
https://raw.githubusercontent.com/marcojpad-hash/agente-cero-costo/main/conector/ESTADO.md
Usa esa versión y esa última actualización como el estado vigente.
Cada vez que tengas información nueva para el equipo, termínala con este bloque:
[EMITIR]
de: <tu nombre>
tipo: actualizacion
mensaje: <lo nuevo, en una línea>
[/EMITIR]
```

## Por qué no es automático del todo

Verificado por búsqueda (2026-11-08): la app estándar de ChatGPT con
GitHub es **de solo lectura** (puede leer el repo, no escribir en él).
El conector de Codex sí tenía escritura, pero era un error de permisos
que OpenAI corrigió en febrero de 2026. El servidor MCP de GitHub sí
tiene herramientas de escritura, pero funciona en Codex, en la API o
en otro cliente MCP, no confirmado en ChatGPT.

Entonces: **recibir es automático** (el modelo lee la URL pública) y
**emitir es por el bloque** (el usuario pega la respuesta aquí).
La vía totalmente automática para emitir es Codex, que sí puede crear
ramas, archivos, issues y PRs en el repo.
