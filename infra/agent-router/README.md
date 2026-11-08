# Router persistente de eventos multiagente

FastAPI + SQLite en volumen persistente. Recibe eventos de GitHub, WhatsApp y conectores de conversación, los persiste y crea una entrega pendiente por cada agente registrado.

## Endpoints

- `GET /health` — salud.
- `POST /v1/events/github` — callback de GitHub Actions.
- `POST /v1/events/conversation` — ingesta de turnos de una conversación.
- `POST /v1/events/whatsapp` — mensajes normalizados del gateway.
- `GET /v1/events/pending?agent_id=claude` — cola pendiente para un agente.
- `POST /v1/events/{event_id}/ack` — ACK/estado de entrega.
- `GET /v1/state` — contadores de estado.

Todas las rutas salvo health requieren `Authorization: Bearer <ROUTER_INGEST_TOKEN>`.

## Configuración

`ROUTER_INGEST_TOKEN`: secreto compartido entre Actions y conectores autorizados.
`ALLOWED_REPOSITORIES`: repositorios admitidos, separados por coma.
`AGENT_WEBHOOKS_JSON`: mapa JSON de agentes a endpoints de callback. En esta primera versión se crean entregas durables y los agentes consultan su cola; el mapa reserva la expansión a push por webhook.

No se guardan credenciales de proveedores en Git. El token debe inyectarse en el host mediante gestor de secretos o archivo de entorno privado.

## Activación

1. Desplegar en host persistente con Docker Compose.
2. Crear token aleatorio largo y configurar el entorno.
3. Configurar GitHub Actions secrets:
   - `AGENT_CALLBACK_URL=https://<host>/v1/events/github`
   - `AGENT_CALLBACK_TOKEN=<mismo token>`
4. Configurar el mismo token para conectores de conversación y WhatsApp.
5. Configurar allowlist y registro de agentes.
6. Probar POST, consultar cola por agente, ACK y reiniciar el contenedor para verificar persistencia.

El servicio enlaza el puerto a localhost. Publicarlo externamente solo detrás de HTTPS reverse proxy/firewall. No exponer SQLite ni el puerto sin TLS.

## Integración de conversaciones

El endpoint `/v1/events/conversation` acepta turnos con `source_agent`, `source_channel`, `event_type`, `content`, `artifact_refs`, `project_ids` y `correlation_id`. El cliente que tenga acceso a la conversación debe publicar cada turno real. No puede extraerse retroactivamente una transcripción de una conversación web si el cliente no la expone.

## Limitaciones actuales

- Router implementado; despliegue persistente y pruebas de red pendientes.
- Los agentes deben implementar un consumidor de cola o un webhook propio.
- El router no invoca por sí mismo APIs de modelos ni suplanta sesiones web.
- El estado COMPLETED debe llegar mediante ACK del adaptador después del trabajo real.
