# Estado global compartido

Última actualización: 2026-11-08
Estado de la propuesta: EN IMPLEMENTACIÓN / NO DESPLEGADA.

## Objetivo

Conseguir que agentes de modelos distintos reciban automáticamente la información nueva del repositorio, la traten como input de trabajo y mantengan continuidad entre sesiones sin usar al usuario como mensajero.

## Arquitectura

- GitHub: fuente de eventos y versionado.
- GitHub Actions: callback ante push, issues, comentarios y PR.
- Router FastAPI + SQLite: recepción autenticada, persistencia y fan-out HTTPS por agente.
- Cola durable: fallback para agentes que no tengan webhook entrante.
- Diario JSONL: continuidad de conversación y decisiones.
- WhatsApp: canal adicional experimental; no reemplaza el bus ni la memoria.

## Estado verificado

- Diseño de eventos y workflow agregados a la rama feature/openai-self-hosted-executor.
- Router FastAPI, Dockerfile y Compose agregados.
- Endpoint de ingesta conversacional agregado al router.
- Registro de la solicitud actual guardado en conversacion/diario/2026-11/2026-11-08.jsonl.
- PR #5 actualizado, en draft, sin merge a main.

## No verificado todavía

- El workflow no está activo en main mientras PR #5 no se integre.
- No se han configurado AGENT_CALLBACK_URL ni AGENT_CALLBACK_TOKEN en GitHub Actions.
- No hay host persistente aprovisionado ni router desplegado.
- No hay endpoints de callback registrados para agentes.
- No se ha probado una entrega real a dos modelos ni ACK de vuelta.
- La transcripción completa del chat no se exporta automáticamente; requiere que el cliente de conversación publique cada turno a /v1/events/conversation.

## Próxima secuencia

1. Integrar la rama después de revisión autorizada.
2. Desplegar router en host persistente con volumen.
3. Configurar secretos de Actions y token de router.
4. Registrar endpoints de agentes que acepten callbacks; para agentes sin webhook, habilitar polling.
5. Conectar el exportador de conversación y probar ingesta turno a turno.
6. Ejecutar prueba de dos agentes con ACK, respuesta cruzada y reinicio.

## Contrato transversal de aprendizaje de fallos

- Contrato obligatorio creado en `gabinete/APRENDIZAJE_DE_FALLOS/CONTRATO_INGENIERIA_INVERSA.md`.
- Índice, reglas aprendidas y plantilla de expediente creados en el mismo directorio.
- Protocolo de continuidad y README general enlazan el Gabinete.
- Todo error atribuible activa reconstrucción, análisis de causa raíz, corrección, prevención, regresión, registro y difusión a agentes pertinentes.
- Ubicación transversal: Gabinete; Steambox continúa reservado al motor U6.
- **Estado:** archivos guardados en `feature/openai-self-hosted-executor`; no integrados en `main`. Aún no existe automatización desplegada que fuerce el cumplimiento ni ACK automáticos de todos los agentes.
