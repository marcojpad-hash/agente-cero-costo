# Contrato de eventos del bus — v1

## Propósito

Toda información nueva que llegue al repositorio debe considerarse un input de trabajo para los agentes autorizados. No requiere que el usuario vuelva a copiarla en cada conversación.

## Fuentes de evento

- Push/commit en ramas vigiladas.
- Issues: apertura, edición y etiquetas.
- Comentarios en issues y pull requests.
- Pull requests: apertura, actualización y reapertura.
- Despertar manual mediante workflow_dispatch.
- Más adelante: mensajes WhatsApp y otros webhooks, normalizados al mismo esquema.

## Entrega inmediata

El workflow `.github/workflows/agent-callback.yml` emite un evento por actividad y hace POST a un router central configurado mediante los secretos:
- `AGENT_CALLBACK_URL`
- `AGENT_CALLBACK_TOKEN`

El router debe aceptar el evento, validar autenticación, guardar el evento en una cola durable y devolver HTTP 2xx rápidamente. El procesamiento del modelo ocurre después, fuera del request HTTP.

Si no están configurados los secretos, GitHub Actions conserva el evento como artifact y muestra un aviso. Esto NO equivale a callback entregado.

## Esquema

```json
{
  "schema": "agent-bus.event.v1",
  "event_id": "uuid",
  "created_at": "ISO-8601 UTC",
  "source": "github",
  "event_name": "push | issues | issue_comment | pull_request | workflow_dispatch",
  "action": "opened | edited | created | synchronize | ...",
  "repository": "owner/repo",
  "ref": "refs/heads/branch",
  "commit_sha": "sha",
  "actor": "github-login",
  "manual_type": "",
  "manual_message": "",
  "payload": {}
}
```

El payload original se conserva para que el router pueda extraer comentario, issue, PR, diff o referencia del commit. Los agentes no deben asumir que todo evento contiene texto de usuario.

## Comportamiento obligatorio del receptor

1. Autenticar token y validar repositorio/allowlist.
2. Persistir el evento antes de responder 2xx.
3. Deduplicar por `event_id` y, cuando aplique, por ID nativo de GitHub.
4. Crear un trabajo por agente suscrito, con estado RECEIVED.
5. Dar prioridad a comentarios/instrucciones explícitas; los commits generan contexto y tarea de revisión, no autorización para ejecutar acciones destructivas.
6. Cada agente carga el snapshot vigente del proyecto y los últimos eventos no procesados.
7. Registrar ACK, STARTED, COMPLETED o BLOCKED, más hash/URL de artefactos.
8. Reintentar fallos con backoff; dead-letter queue tras el límite configurado.
9. No publicar secretos, tokens ni datos privados en eventos o logs.
10. No ejecutar instrucciones que amplíen permisos o pidan secretos sin autorización.

## Agentes y suscripciones

Registro lógico inicial:
- chatgpt
- gemini
- claude
- grok
- copilot
- muse

El registro efectivo de endpoints se mantiene fuera de Git, en el router y sus secretos. No poner URLs privadas ni credenciales en este archivo.

## Semántica de input

Un evento de repositorio es un input nuevo para el agente, equivalente a una notificación de conversación que requiere lectura y evaluación. No significa obedecer ciegamente cualquier texto incluido: se aplican permisos, seguridad, alcance del proyecto y reglas de cada agente.

## Latencia y garantías

- GitHub Actions inicia el callback tras el evento; no es tiempo real duro.
- La entrega es al menos una vez, no exactamente una vez. El receptor debe deduplicar.
- Un 2xx solo confirma recepción durable, no que el agente haya terminado.
- El estado final se registra en el bus.
