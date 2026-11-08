# Provisioning de sesión Agents API

Este componente aún no crea la sesión automáticamente. La aplicación que administra la sesión debe:

1. Autenticarse con una clave de aplicación OpenAI que tenga los permisos mínimos documentados: `api.agents.read`, `api.agents.write` y `api.responses.write`.
2. Crear una sesión con `agent.model` e `instructions`, y `environment: { type: "self_hosted", workspace_directory: "/workspace" }`.
3. Guardar `session.id`, `session.environment.id` y `session.environment.remote_url` en un almacén de secretos/estado seguro.
4. Crear una clave de entorno restringida desde Agents > Environments y pasarla al contenedor como `CODEX_API_KEY`.
5. Iniciar el executor y esperar el evento `agent.session.environment.connected`.
6. Enviar el input del usuario a la sesión y consumir el stream de eventos.

Referencia oficial y ejemplo SDK: https://developers.openai.com/api/docs/guides/agents-api/environments/self-hosted

La clave de aplicación nunca se pasa al sandbox. La clave restringida del entorno nunca se incluye en el repositorio. No activar este flujo hasta disponer de proyecto API y credenciales con permisos correctos.
