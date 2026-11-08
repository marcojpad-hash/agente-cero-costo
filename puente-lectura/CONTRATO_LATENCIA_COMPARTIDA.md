# Contrato de latencia compartida entre agentes

**Estado:** propuesta operativa para integrar al Puente MCP.  
**Objetivo:** continuidad entre aplicaciones sin activar modelos ni provocar búsquedas innecesarias.

## Principio

Los agentes permanecen **disponibles en latencia**, no ejecutándose. Cambiar de ChatGPT a Muse, Grok, Copilot, Gemini u otro host no debe exigir al usuario explicar dónde está el estado compartido ni ordenar una búsqueda manual del repositorio.

La fuente común es el servicio MCP y su estado persistente. GitHub conserva artefactos y trazabilidad; no es necesario que cada agente navegue GitHub en cada turno.

## Tres estados

1. **LATENCIA (predeterminado).** El agente no genera texto, no llama a un LLM, no hace búsquedas web, no inicia tareas ni consume tokens por estar conectado. El servicio conserva mensajes, eventos y punteros de continuidad.
2. **LECTURA DE CONTEXTO.** Cuando un agente se activa porque el usuario abre/inicia una interacción, consulta el MCP una sola vez: identidad/estado, mensajes pendientes y resumen vigente. No rastrea todos los repositorios ni vuelve a investigar lo ya documentado.
3. **ACTIVIDAD DELEGADA.** Solo cuando el usuario lo pide o existe una tarea explícitamente delegada. El agente responsable trabaja; los demás siguen en latencia. La comunicación entre agentes ocurre por el bus, no por activaciones recursivas.

## Contrato de entrada al activarse

Al comenzar una sesión o retomar trabajo, el host debe:
- registrarse/actualizar presencia;
- leer el manifiesto de continuidad vigente;
- consultar su inbox desde el último cursor/ACK;
- revisar si hay una tarea dirigida a él o un bloqueo que requiera su intervención;
- responder al usuario con el contexto ya disponible, sin pedirle que repita el repositorio o la ruta.

Si no hay novedad, termina la lectura y trabaja normalmente. No debe iniciar búsquedas solo por haber encontrado un heartbeat.

## Reglas para evitar tormentas de activación

- **Heartbeat no es una orden:** nunca despierta un modelo ni crea una tarea.
- **Broadcast informativo no es una orden:** queda disponible en el inbox; no provoca ejecución automática.
- **Direct message no es ejecución automática:** se procesa en el siguiente punto de activación del agente destinatario, salvo que el host tenga una política explícita de notificación de baja frecuencia.
- **Un solo responsable por tarea:** toda tarea delegada tiene `task_id`, `owner_agent`, `status`, `created_by` y criterio de cierre. Los demás solo aportan si se les asigna o se solicita.
- **Sin cascadas:** una respuesta no genera por sí sola otra tarea. Se prohíben los bucles A→B→A sin una condición de cierre.
- **Deduplicación:** `event_id` y `task_id` idempotentes; ACK después de procesar, no antes.
- **Prioridades:** `FYI` (solo conservar), `NEXT_ACTIVATION` (mostrar al reabrir), `ACTION_REQUEST` (requiere asignación explícita), `URGENT` (solo si el usuario definió previamente qué significa urgente y autorizó notificación).
- **Sin notificaciones por defecto:** no push, polling de LLM, cron de búsquedas ni llamadas a APIs externas mientras el agente está en latencia.

## Qué se comparte para continuidad

El manifiesto común debe ser breve y apuntar a artefactos:
- proyecto y objetivo activo;
- estado actual y último hito verificado;
- decisiones y restricciones vigentes;
- tareas abiertas con responsable y próximo paso;
- referencias exactas a archivos/commits;
- fecha de actualización y agente que actualizó.

No duplicar archivos grandes ni copiar secretos. Los documentos fuente siguen en sus repositorios.

## Separación de responsabilidades

- **Bus MCP:** almacena y entrega mensajes/estado; no razona ni decide activar modelos.
- **Agente anfitrión:** consulta al activarse y decide qué es pertinente para su conversación.
- **Agente delegado:** trabaja solo sobre una asignación explícita.
- **Orquestador liviano:** puede mantener punteros/colas y deduplicar eventos sin invocar un LLM. No debe buscar por iniciativa propia.
- **Usuario:** cambia de aplicación sin tener que transportar manualmente el contexto.

## Límite técnico importante

Un servidor MCP no puede obligar a una aplicación a consultar herramientas al abrirse ni inyectar contexto en todos los chats. Cada host debe configurar el MCP y adoptar el contrato de lectura al inicio/retoma. Si el host no admite MCP remoto o no ejecuta herramientas automáticamente al iniciar, se necesita un adaptador o una instrucción de arranque del host. No declarar continuidad automática hasta probarla en ese host.

## Pruebas de aceptación

1. Agente A guarda un estado de trabajo y referencia a sus artefactos.
2. A queda en latencia: no hay llamadas a LLM ni búsquedas posteriores.
3. Usuario abre agente B en otra aplicación.
4. B consulta una vez el MCP, obtiene estado y tareas pendientes sin pedir al usuario la ruta del repositorio.
5. B no inicia búsquedas ni tareas si el estado solo es informativo.
6. Si existe una tarea asignada a B, B la muestra/continúa según las reglas del host; otros agentes permanecen quietos.
7. La misma prueba se repite con un tercer host.
8. Se verifica ausencia de duplicados, cascadas y notificaciones no autorizadas.

**Criterio de éxito:** continuidad recuperada al cambiar de aplicación, sin actividad de modelos en segundo plano ni intervención manual para localizar la información.
