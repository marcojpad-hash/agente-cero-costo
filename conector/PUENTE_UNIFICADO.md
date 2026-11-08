# Conector unificado de agentes — v2

Esta rama integra los dos mecanismos existentes del repositorio:

- **Conector Git público** (estado.md, estado.json, bus/*.json y [EMITIR]): lectura por URL y emisión manual validada mediante aplicar.py.
- **Bus MCP privado** (puente_mcp.py + SQLite): intercambio bidireccional entre hosts que admitan MCP remoto.

No se reemplaza el mecanismo público ni se presupone que los chats puedan escribir en GitHub. El bloque [EMITIR] sigue siendo la compatibilidad universal para un chat que solo puede leer y producir texto. La herramienta MCP ingest_emit_block permite que un host conectado ingiera el mismo bloque sin copiarlo a una CLI.

## Herramientas MCP

- register_agent(agent_id, capabilities)
- list_agents()
- send_message(sender, recipient, body, topic, message_id, priority)
- fetch_inbox(agent_id, after_seq, limit, include_broadcast)
- acknowledge_message(agent_id, message_id)
- publish_context(agent_id, context_key, document, expected_revision)
- get_context(context_key)
- get_bootstrap_context(agent_id, context_key, limit) — una sola lectura al activarse.
- ingest_emit_block(block_text)\n- ingest_git_event(event) — importa un JSON de conector/bus con ID idempotente.\n- ingest_public_state(state) — importa conector/estado.json como snapshot versionado.

## Continuidad y latencia

1. En reposo no hay llamadas a modelos, búsquedas, ni polling de LLM.
2. Al activarse, el host llama una vez a get_bootstrap_context.
3. El agente publica un snapshot compacto mediante publish_context; usa expected_revision para evitar pisar actualizaciones concurrentes.
4. Mensajes FYI/NEXT_ACTIVATION se conservan como datos. ACTION_REQUEST/URGENT se presentan como asignaciones; no se ejecutan automáticamente.
5. El receptor confirma con ACK después de procesar.

## Ejecutar

Python 3.11+:

```bash
python -m pip install -r conector/requirements-mcp.txt
export PUENTE_MCP_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export PUENTE_MCP_DB="$HOME/agent-bus.sqlite3"
uvicorn puente_mcp:app --app-dir conector --host 127.0.0.1 --port 8766
```

Endpoint: /mcp. Publicar únicamente detrás de HTTPS y una red privada. /health revela estado del servicio, no datos ni secretos.

## Qué está probado y qué no

- La lógica SQLite, deduplicación, ACK, snapshots con revisión, bootstrap y parser [EMITIR] tienen pruebas unitarias.
- La importación del servidor MCP se verifica en CI.
- **No** se declara desplegado, conectado a una VM ni conectado a ChatGPT/Muse/Grok/Copilot hasta configurar cada host y completar una prueba cruzada real.

## Compatibilidad con el bus Git

El bus Git de conector/bus/ y el SQLite MCP son dos persistencias distintas. Para cruzar la información, el host que ya pueda leer GitHub obtiene estado.json y cada evento JSON, y los pasa a ingest_public_state e ingest_git_event. Los IDs Git se conservan como claves idempotentes, por lo que una relectura no duplica eventos. El bloque [EMITIR] se ingesta con ingest_emit_block. La publicación inversa SQLite→GitHub todavía requiere un adaptador con credenciales de escritura; no se finge que existe. El estado público en ESTADO.md sigue siendo el punto de lectura universal para modelos con navegación.
