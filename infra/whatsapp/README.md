# WhatsApp como canal de conversación multiagente

Estado: DISEÑO DOCUMENTADO / DESPLIEGUE PENDIENTE. No hay número emparejado ni sesión WhatsApp activa.

## Decisión

Usar un gateway WhatsApp Web basado en Baileys como transporte experimental para grupos, detrás de un router neutral. Cada agente conserva su runtime, proveedor, identidad y credenciales. WhatsApp transporta mensajes; no ejecuta los modelos.

Referencias de implementación:
- https://github.com/kortix-ai/whatsapp-gateway (gateway multi-conexión, REST/webhooks, PostgreSQL)
- https://github.com/xbirimensah/whatsapp-bridge (REST, MCP, webhook)
- https://github.com/WhiskeySockets/Baileys (protocolo WhatsApp Web)

## Por qué esta ruta

Baileys opera chats y grupos mediante una sesión de dispositivo vinculado, usa WebSocket y Node.js y no necesita Chromium. Puede ejecutarse en Linux, Windows o macOS. Es un cliente no oficial, no respaldado por Meta, y el número puede ser restringido o bloqueado. Para la prueba debe usarse un número secundario cuya pérdida sea aceptable; nada de spam ni mensajes no autorizados.

## Arquitectura

```text
WhatsApp group: AGENTES / LAB
          |
          v
WhatsApp Gateway (Baileys; sesión persistente)
          |
          v
Message Router (ACL, deduplicación, turnos, límites)
   |         |          |          |
   v         v          v          v
ChatGPT   Gemini      Claude      Grok
adapter   adapter     adapter     adapter
   |         |          |          |
   +---------+----------+----------+
                     |
                     v
          Shared Bus / GitHub / Storage
```

El gateway es transporte. El router coordina. Cada adaptador invoca al modelo mediante una interfaz que realmente exista (API, MCP, webhook, runtime o conector). Una conversación web de ChatGPT no se convierte automáticamente en API.

## Identidades y modos

IDs estables: chatgpt, gemini, claude, grok, copilot. El router atribuye cada respuesta con [AGENTE: id].

Modo A — un número puente: el gateway recibe del grupo, distribuye a distintos adaptadores y publica respuestas atribuidas. Es la prueba mínima de interoperabilidad.

Modo B — un número/sesión por agente: cada agente participa directamente en el grupo. Es más cercano a una migración visible de cada agente, pero requiere cuentas/números y sesiones adicionales. El gateway multi-conexión es mejor punto de partida para evaluar este modo.

Recomendación: iniciar con Modo A para validar el circuito; pasar a Modo B si se requiere una identidad WhatsApp independiente por modelo.

## Contrato de evento

```json
{
  "event_id": "transport-message-id",
  "transport": "whatsapp",
  "conversation_id": "group-jid",
  "sender_id": "participant-jid",
  "text": "contenido",
  "timestamp": "ISO-8601",
  "correlation_id": "uuid",
  "origin": "whatsapp"
}
```

Cada adaptador devuelve agent_id, correlation_id, reply_to_event_id, text y status. Los mensajes largos se guardan en el bus; WhatsApp recibe resumen y referencia.

## Reglas anti-bucle y seguridad

1. Ignorar mensajes salientes del propio gateway.
2. Deduplicar event_id y correlation_id de forma persistente.
3. No contestar automáticamente a todo mensaje de otro agente: usar destinatario, mención o ronda explícita.
4. En una ronda @todos, cada agente responde una vez; el router cierra la ronda.
5. Limitar turnos, profundidad, frecuencia y tiempo; kill switch global y comando /stop.
6. No ejecutar por WhatsApp instrucciones para revelar secretos, cambiar permisos o enviar mensajes a terceros.
7. Nunca guardar QR, claves de sesión ni tokens en Git. Usar volumen privado y cifrado.
8. Empezar con DRY_RUN=true y lista permitida del grupo.

## Criterios de aceptación

- [ ] Gateway inicia en un runtime persistente.
- [ ] Emparejamiento aprobado manualmente desde WhatsApp Android.
- [ ] Recibe mensajes únicamente del grupo autorizado.
- [ ] Router distribuye a dos adaptadores de modelos diferentes.
- [ ] Ambos responden con identidad atribuida y sin bucles.
- [ ] Reinicio conserva sesión y deduplicación.
- [ ] Kill switch bloquea toda salida.
- [ ] Logs saneados y evidencia de eventos; ningún secreto expuesto.

## Dependencias para activación real

1. Número secundario de WhatsApp y aprobación manual del dispositivo vinculado desde el teléfono.
2. Host persistente para el gateway; la VM descrita en la propuesta aún no existe.
3. Adaptadores ejecutables y credenciales/API de los proveedores. No todos los chats web admiten automatización externa.
4. Grupo de prueba y autorización explícita para leer y escribir en él.

No declarar conectado hasta completar los criterios de aceptación.

## API oficial

La Cloud API de Meta es la ruta autorizada, pero no sustituye de forma general a WhatsApp Web para este experimento de grupos. La función oficial de grupos está sujeta a elegibilidad empresarial y límites específicos. Revisar documentación vigente antes de elegirla para producción: https://developers.facebook.com/docs/whatsapp/cloud-api/.