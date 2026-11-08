# Entorno propio de ejecución para el agente OpenAI

Estado: **implementación versionada; despliegue y conexión real pendientes**.

## Qué resuelve

Este módulo prepara el lado de ejecución para que un agente de OpenAI trabaje sobre un directorio persistente alojado fuera del chat. Usa el flujo oficial **Agents API + self-hosted sandbox**:

1. La aplicación crea una sesión de agente con `environment.type = "self_hosted"`.
2. La sesión devuelve `environment.id` y `environment.remote_url`.
3. El entorno Linux ejecuta `codex exec-server` con esos valores.
4. El executor mantiene una conexión WebSocket saliente con OpenAI; no requiere abrir un puerto entrante.
5. El volumen `/workspace` conserva archivos entre reinicios del contenedor/VM.

Documentación oficial: https://developers.openai.com/api/docs/guides/agents-api/environments/self-hosted

## Distinción importante

Esto crea un agente de OpenAI basado en Agents API (modelo seleccionable en la API, por ejemplo `gpt-6-astra`) conectado a infraestructura propia. **No conecta retroactivamente esta conversación de ChatGPT ni convierte el runtime temporal de esta sesión en una VM persistente.** Es un agente/runtime separado y el uso de la API se factura según las condiciones de la API; una suscripción ChatGPT no debe suponerse como crédito API.

## Componentes

- `compose.yaml`: contenedor Linux con volumen persistente y executor.
- `.env.example`: nombres de variables, sin valores secretos.
- `entrypoint.sh`: valida configuración y conecta el executor.
- `provisioning/README.md`: contrato para el servicio externo que crea sesiones y entrega credenciales de entorno.
- `security/ACCESS_MODEL.md`: aislamiento por agente y límites de permisos.

## Despliegue

Requiere una VM Linux persistente (Ubuntu 24.04 recomendado), Docker Engine + Compose y acceso saliente HTTPS/WSS a OpenAI. El directorio de trabajo persistente se monta en `/srv/agentes/openai-workspace`.

1. Copiar esta carpeta a la VM.
2. Crear el archivo `.env` fuera del repositorio con `CODEX_API_KEY`, `CODEX_REMOTE_URL` y `CODEX_ENVIRONMENT_ID`.
3. Asegurar permisos de lectura solo para la cuenta de servicio.
4. Ejecutar `docker compose up -d --build`.
5. Verificar `docker compose logs -f executor` y confirmar el evento `agent.session.environment.connected` en el flujo de eventos de la aplicación.

No se debe colocar `OPENAI_API_KEY` de la aplicación dentro del contenedor executor. La clave de entorno debe ser una clave restringida que solo permita conectar entornos. No guardar claves en Git, imágenes, logs ni Issues.

## Lo que falta para activarlo

- Crear el proyecto/servicio de Agents API y sus claves restringidas en la plataforma OpenAI.
- Aprovisionar la VM persistente en un proveedor autorizado.
- Crear una sesión Agents API y entregar su `environment.id` y `remote_url`.
- Conectar y probar el executor desde la VM real.
- Registrar proveedor, ubicación y estado de conexión sin exponer secretos.

La sesión y el executor deben corresponder al mismo entorno. Cada sesión self-hosted necesita su propio environment ID y executor; reutilizar imagen y directorio base es posible, pero no significa que varias sesiones compartan automáticamente un mismo espacio de trabajo.

## Resultado esperado

El agente OpenAI API puede ejecutar comandos y leer/escribir archivos en el volumen persistente de la VM, mientras GitHub continúa como plano común de coordinación. Los otros agentes se conectan a través de sus adaptadores propios (SSH/SFTP, Git o API de archivos), con identidades y permisos separados.
