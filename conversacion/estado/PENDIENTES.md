# Pendientes de activación

- [ ] Revisar y fusionar PR #5 cuando se autorice.
- [ ] Aprovisionar host persistente y desplegar infra/agent-router.
- [ ] Configurar GitHub Actions secrets AGENT_CALLBACK_URL y AGENT_CALLBACK_TOKEN.
- [ ] Establecer ALLOWED_REPOSITORIES.
- [ ] Registrar endpoint HTTPS y credencial de callback por cada agente disponible.
- [ ] Implementar consumidores/pollers para agentes que no acepten webhooks.
- [ ] Conectar exportador de turnos de ChatGPT/Gemini/otros clientes a /v1/events/conversation.
- [ ] Conectar gateway WhatsApp a /v1/events/whatsapp.
- [ ] Probar dos agentes distintos: callback, lectura, respuesta, ACK y deduplicación.
- [ ] Reiniciar router y confirmar persistencia de eventos y cursores.
