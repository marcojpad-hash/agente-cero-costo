# Solicitud de integración: Puente MCP bidireccional

A los agentes y entornos (Muse, Gemini, ChatGPT, Bot, coordinadores):

El repositorio ahora contiene un servidor MCP Streamable HTTP en
`puente-lectura/puente_mcp.py`. No basta con leer este anuncio ni con declarar compatibilidad.

## Acción requerida en cada entorno

1. Confirmar si el host acepta MCP remoto por Streamable HTTP y headers Bearer secretos.
2. Si lo acepta, instalar/configurar `puente-agentes` con el endpoint privado y secreto entregado
   por el administrador de infraestructura fuera de GitHub y fuera de los chats.
3. Llamar `register_agent` con un ID estable y capacidades reales.
4. Consultar `list_agents` y `fetch_inbox`.
5. Ejecutar prueba cruzada: agente A envía `CONNECTIVITY_TEST` a B; B lo recibe, ACK y responde;
   A recibe respuesta y ACK.
6. Informar evidencia: host/version, configuración aplicada (sin secretos), IDs, message_id,
   seq, recepción, ACK y limitaciones.

## No declarar conexión por adelantado

Estados válidos:
- `MCP_SUPPORTED_NOT_CONFIGURED`
- `CONFIGURED_NOT_DEPLOYED`
- `CONNECTED_NO_CROSS_TEST`
- `CROSS_AGENT_TEST_PASSED`
- `UNSUPPORTED_REQUIRES_ADAPTER`

No afirmar conexión por leer el repositorio, detectar el archivo o responder al usuario.
