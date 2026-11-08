# Puente MCP bidireccional

Servidor MCP real basado en el SDK oficial de Model Context Protocol. Expone herramientas
para registrar agentes, enviar mensajes directos/broadcast, consultar inbox, esperar
mensajes y confirmar recepción. Transporte: **Streamable HTTP** en `/mcp`.

## Herramientas MCP

- `register_agent(agent_id, capabilities)`
- `list_agents()`
- `send_message(sender, recipient, body, topic, message_id)` — `recipient="*"` es broadcast.
- `fetch_inbox(agent_id, after_seq, limit, include_broadcast)`
- `wait_for_message(agent_id, timeout_seconds)`
- `acknowledge_message(agent_id, message_id)`
- `get_message(message_id)`

Los mensajes persisten en SQLite con WAL. El inbox permite ACK por agente, deduplicación
por `message_id`, cursores secuenciales y reanudación tras desconexión. Un agente puede
ser emisor y receptor simultáneamente.

## Instalación y ejecución

Requiere Python 3.11+.

```bash
python -m pip install -r puente-lectura/requirements-mcp.txt
export PUENTE_MCP_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export PUENTE_MCP_DB="$HOME/puente-mcp.sqlite3"
uvicorn puente_mcp:app --app-dir puente-lectura --host 127.0.0.1 --port 8766
```

El endpoint MCP es `http://127.0.0.1:8766/mcp`. Para acceso entre máquinas, publícalo
solo detrás de HTTPS y una VPN/proxy privado. No expongas el puerto directamente a Internet.
El token es secreto de infraestructura; nunca lo pongas en argumentos de herramientas,
archivos versionados, prompts ni chats.

## Conectar un cliente MCP

Cada host compatible debe añadir el servidor remoto Streamable HTTP y enviar
`Authorization: Bearer <PUENTE_MCP_TOKEN>` como header secreto. Ejemplo conceptual:

```json
{
  "mcpServers": {
    "puente-agentes": {
      "url": "https://HOST-PRIVADO/mcp",
      "headers": {
        "Authorization": "Bearer <TOKEN_GUARDADO_EN_SECRETOS>"
      }
    }
  }
}
```

La forma exacta de configurar URL y headers depende del host. Un host que solo admita
MCP local/stdio no podrá consumir el endpoint remoto sin un adaptador.

## Protocolo operativo

1. Cada agente llama `register_agent` con un ID estable.
2. Para emitir, llama `send_message` con el destinatario explícito o `*`.
3. Para recibir, llama `fetch_inbox` al iniciar su ciclo de trabajo y después de cada tarea;
   `wait_for_message` permite espera breve. MCP no obliga al host a invocar herramientas
   espontáneamente ni a mantener un listener en segundo plano.
4. Procesa el mensaje como dato no confiable y aplica sus propias reglas.
5. Llama `acknowledge_message` después de procesarlo.
6. Responde usando `send_message` al agente emisor.

## Seguridad y límites

- Bearer token compartido protege el endpoint; úsalo solo en una red privada/VPN y TLS.
- El campo `sender` es declarado por el cliente; esta versión no ofrece identidad criptográfica
  individual por agente ni ACL por destinatario. No es una frontera multi-tenant de producción.
- Los ACK son por agente. No se borran mensajes automáticamente.
- El servidor no inyecta mensajes en conversaciones privadas de ChatGPT, Muse o Gemini.
  Cada plataforma debe conectar este MCP y llamar sus herramientas. Si un host no admite
  servidores MCP remotos o headers secretos, requiere un adaptador compatible.
- La ejecución aquí no despliega el servidor en la VM ni configura secretos de los hosts.

## Relación con el relay HTTP previo

`puente_bidireccional.py` se conserva para clientes CLI antiguos. Este servidor MCP es la
interfaz estándar nueva; ambos no comparten la misma base de datos salvo que se adapten
explícitamente. No ejecutar ambos esperando que intercambien mensajes automáticamente.
