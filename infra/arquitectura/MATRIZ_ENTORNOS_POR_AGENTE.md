# Matriz de entornos por agente — federación operativa

Estado: **contrato y adaptadores definidos; conexiones externas pendientes de verificación**.

## Regla principal

No exigir que todos los agentes usen el mismo sistema operativo, proveedor, modelo, IDE o runtime. Cada agente trabaja en su entorno nativo o en el equivalente ejecutable que sí tenga disponible. La interoperabilidad se resuelve en la capa de intercambio, no intentando meter todos los modelos dentro de una sola máquina.

GitHub es el plano de coordinación, registro y versionado. El almacenamiento compartido persistente es la capa de datos. Cada agente conserva su executor, credenciales e identidad.

## Despliegue por carriles

| Agente | Carril de ejecución | Adaptador de intercambio | Estado |
|---|---|---|---|
| ChatGPT conversación | Herramientas y conectores disponibles en el chat; no se presume shell persistente | GitHub API / bus / archivos versionados | Conector GitHub disponible; shell persistente no acreditado |
| Agente OpenAI API | Agents API + self-hosted sandbox executor | Volumen persistente + GitHub + API de intercambio | Implementación preparada en infra/openai-self-hosted/; despliegue pendiente |
| Muse | Runtime que ofrezca Muse (terminal, VM o contenedor propio) | GitHub + SFTP/HTTPS cuando esté disponible | Pendiente de detectar y probar |
| Gemini | Runtime propio o contenedor Linux autorizado | GitHub + SFTP/HTTPS cuando esté disponible | Pendiente de detectar y probar |
| Grok | Runtime propio o contenedor Linux autorizado | GitHub + SFTP/HTTPS cuando esté disponible | Pendiente de detectar y probar |
| Copilot | Runtime propio o Codespaces/entorno autorizado | GitHub + SFTP/HTTPS cuando esté disponible | Pendiente de detectar y probar |

No afirmar conexión de un agente por haber documentado su adaptador. Solo cambiar el estado a CONECTADO después de una prueba de lectura y escritura con identidad propia.

## Contrato común de intercambio

Todo agente debe poder implementar al menos una de estas vías:

1. **Git nativo:** clonar, leer, crear rama, commit y PR con identidad propia.
2. **SFTP/SSH:** leer y escribir solo en su carpeta y en el espacio compartido autorizado.
3. **HTTPS API:** leer/escribir objetos con token restringido a su identidad.
4. **Carpeta sincronizada:** usar un agente de sincronización local que suba cambios a GitHub o al almacenamiento compartido.

El adaptador es intercambiable. No bloquear un agente por no tener SSH si puede usar Git o HTTPS.

## Estructura del espacio común

    /shared/
      bus/                 # eventos y mensajes inmutables
      exchange/<agent>/    # entregas de cada agente
      projects/<project>/  # artefactos compartidos por proyecto
      state/               # estado, cursores y manifiestos
      audit/               # pruebas de acceso y cambios

Cada agente tiene identidad y carpeta privada. Escritura cruzada solo donde la autorización del recurso lo permita. No montar secretos ni homes privados en el directorio común.

## Protocolo de trabajo

1. Al activarse, el agente consulta el bus y el estado del proyecto.
2. Lee instrucciones y autorizaciones vigentes antes de actuar.
3. Trabaja en su propio runtime y rama/carpeta de agente.
4. Publica artefactos y un manifiesto de cambios en exchange/<agent>/.
5. Registra hash, fecha, alcance, pruebas y estado: PREPARADO, EJECUTADO, VERIFICADO o BLOQUEADO.
6. El siguiente agente consume el artefacto directamente desde la fuente común. El usuario no actúa como mensajero.

## Prueba mínima de interoperabilidad

- Dos agentes con runtimes diferentes.
- Identidades distintas.
- Ambos leen el mismo manifiesto.
- Agente A escribe un archivo de prueba en su carpeta de intercambio.
- Agente B lo lee, verifica hash y escribe respuesta.
- A lee la respuesta.
- Reiniciar ambos runtimes y repetir lectura para demostrar persistencia.
- Guardar evidencias en audit/.

## Regla para el operador

Si el runtime preferido no está disponible, generar y usar el equivalente que sí pueda ejecutar ese agente (contenedor, VM, Codespace, runner, proceso local o adaptador Git/HTTPS). No detener el trabajo en una incompatibilidad de plataforma. No afirmar que un runtime temporal es una VM persistente ni que un adaptador preparado ya está conectado.

La infraestructura común no debe depender de que todos los agentes compartan sistema operativo. Debe depender de un protocolo pequeño, abierto y verificable.
