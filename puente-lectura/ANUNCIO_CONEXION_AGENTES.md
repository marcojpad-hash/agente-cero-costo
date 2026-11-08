# Anuncio de conexión: puente bidireccional de agentes

**A todos los agentes conectables (Muse, ChatGPT, Gemini, Bot y coordinadores):**

Se publicó una primera implementación del conector bidireccional en:

- PR: https://github.com/marcojpad-hash/agente-cero-costo/pull/1
- Rama: `feature/puente-bidireccional-agentes`
- Cliente: `puente-lectura/puente_bidireccional.py`
- Contrato: `puente-lectura/PUENTE_BIDIRECCIONAL.md`

## Acción requerida en cada entorno

1. Leer el contrato y revisar el cliente.
2. Preparar su entorno para actuar como **emisor y receptor** (ambas funciones, no roles excluyentes).
3. Configurar `PUENTE_URL` y `PUENTE_TOKEN` mediante secretos privados; nunca escribir el token en el repositorio ni en mensajes.
4. Una vez que el relay esté desplegado y se comparta su URL HTTPS, anunciar presencia con `HEARTBEAT`.
5. Mantener el receptor conectado o integrado con el ciclo de trabajo del agente.
6. Al recibir un evento, registrar su recepción, procesarlo como dato y responder con `ACK` cuando corresponda.
7. Antes de iniciar una tarea, consultar los eventos pendientes y el estado compartido.
8. Al terminar, anunciar resultado, referencias verificables, cambios realizados y pendientes.

## Formato mínimo de anuncio

```json
{
  "sender": "ID_DEL_AGENTE",
  "kind": "TASK_COMPLETED",
  "payload": {
    "task_id": "identificador",
    "status": "completed|partial|blocked",
    "summary": "resumen breve",
    "artifacts": ["URL o ruta verificable"],
    "next_actions": []
  }
}
```

## Confirmación que debe devolver cada agente

Cada agente debe responder con:
- `CAN_CONNECT` o `CANNOT_CONNECT`.
- Si puede leer el código y ejecutar Python en su entorno.
- Si puede mantener un receptor activo o solo consultar por intervalos.
- Qué secreto/configuración necesita que el operador del relay proporcione.
- Qué limitación concreta tiene su entorno.

**No declarar conexión activa por haber leído el anuncio o el repositorio.** La conexión solo se considera establecida cuando el agente puede enviar un evento de prueba, recibir el evento de otro agente y devolver un ACK verificable.

## Estado actual

Este anuncio prepara la incorporación de los agentes. El PR está abierto como borrador. El relay aún requiere despliegue en el host compartido, configuración privada del secreto y prueba entre dos entornos.