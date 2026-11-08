# Modo de latencia compartida

La especificación operativa está en [CONTRATO_LATENCIA_COMPARTIDA.md](CONTRATO_LATENCIA_COMPARTIDA.md).

Regla central: los agentes no deben permanecer ejecutando modelos para "estar pendientes". El bus conserva estado y mensajes en reposo. Cada agente consulta el estado común al activarse o retomar una sesión; solo el responsable de una tarea explícitamente delegada trabaja. Heartbeats y broadcasts informativos no despiertan modelos.

El MCP no puede inyectar contexto automáticamente en cualquier aplicación: cada host debe conectarlo y adoptar la lectura al inicio/retoma. La continuidad entre hosts se considera aprobada únicamente después de una prueba real de cambio de aplicación.
