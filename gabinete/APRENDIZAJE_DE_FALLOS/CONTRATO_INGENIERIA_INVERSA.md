# Contrato operativo: ingeniería inversa obligatoria de fallos

**Estado:** propuesta incorporada a rama de trabajo; pendiente de revisión e integración.  
**Ámbito:** todos los agentes, modelos, harnesses, automatizaciones y operadores que trabajen en proyectos conectados al Gabinete.  
**Ubicación canónica:** `gabinete/APRENDIZAJE_DE_FALLOS/`.

## 1. Regla no negociable

Cuando un agente cometa un error, entregue un resultado incorrecto, omita una instrucción, afirme una ejecución no realizada, repita una búsqueda que ya debía estar resuelta o provoque que el usuario tenga que detectar y corregir un fallo operativo, ese agente DEBE realizar ingeniería inversa del incidente.

No basta con disculparse, corregir superficialmente el resultado ni trasladar al usuario la investigación. El agente responsable debe reconstruir cómo llegó al error, localizar la causa raíz, corregir el mecanismo que lo produjo y dejar evidencia reutilizable para que ningún otro agente tenga que descubrir lo mismo desde cero.

La obligación aplica también cuando el fallo se detecta por otro agente, una prueba, una auditoría o el usuario. No se exige culpar a un agente cuando la evidencia no permite atribución; sí se exige investigar el fallo del sistema.

## 2. Procedimiento obligatorio

Ante cada incidente, el agente responsable debe:

1. **Contener:** detener la propagación del dato, acción o supuesto incorrecto. Identificar qué entregables, decisiones o agentes pudieron verse afectados.
2. **Reconstruir:** recuperar la secuencia exacta de entradas, instrucciones vigentes, contexto disponible, decisiones, herramientas llamadas, parámetros, respuestas y cambios de archivos. Usar logs, commits, diffs, trazas y artefactos; no reconstruir de memoria si existen evidencias.
3. **Reproducir:** intentar reproducir el fallo en condiciones controladas. Si no es reproducible, documentar las condiciones faltantes y el grado de certeza.
4. **Localizar causa raíz:** distinguir causa inmediata, causa contribuyente y causa sistémica. Revisar, entre otros: lectura incompleta, contexto omitido, búsqueda insuficiente, referencia obsoleta, inferencia presentada como hecho, herramienta equivocada, parámetros incorrectos, permisos, límites del runtime, validación ausente y transferencia defectuosa entre agentes.
5. **Corregir:** reparar el resultado afectado y el procedimiento, instrucción, adaptador, test, contrato o mecanismo que permitió el fallo. No modificar archivos canónicos o áreas protegidas sin autorización.
6. **Prevenir:** añadir una regla, validación automatizada, test de regresión, alerta o referencia operativa concreta. Evitar soluciones que dependan de que el usuario vuelva a detectar el mismo problema.
7. **Verificar:** ejecutar la prueba que demuestra la corrección y registrar el resultado. Si no puede ejecutarse, marcar explícitamente como PENDIENTE_DE_VERIFICACIÓN; nunca declarar resuelto.
8. **Difundir:** registrar el aprendizaje en el Gabinete y notificarlo por el bus a los agentes y proyectos afectados. Cada agente receptor debe leer la corrección antes de repetir la tarea relacionada y emitir ACK.
9. **Cerrar:** entregar al usuario un resumen breve con causa raíz, corrección, evidencia, estado de verificación y referencia persistente. No pedir al usuario que haga la ingeniería inversa que corresponde al agente.

## 3. Registro obligatorio de cada incidente

Crear un expediente por incidente en `gabinete/APRENDIZAJE_DE_FALLOS/incidentes/`, con identificador estable y fecha. Usar esta plantilla:

- ID y fecha/hora UTC.
- Proyecto, agente responsable y agentes afectados.
- Severidad e impacto observado.
- Resultado esperado y resultado real.
- Evidencias y referencias exactas (commit, archivo, líneas, ejecución, evento o conversación).
- Cronología reproducible.
- Causa inmediata, causas contribuyentes y causa raíz.
- Qué información o comprobación faltó y por qué.
- Corrección aplicada (archivos, commits, cambios).
- Prevención incorporada (regla, test, automatización o control).
- Prueba de regresión y resultado.
- Estado: ABIERTO, CONTENIDO, EN_INVESTIGACIÓN, CORREGIDO_PENDIENTE_DE_PRUEBA, VERIFICADO o NO_REPRODUCIBLE.
- Lección operativa reutilizable y agentes notificados/ACK.

Los expedientes son append-only en lo sustantivo: las rectificaciones se agregan con fecha y referencia; no se borra el historial para aparentar que el error no ocurrió. No incluir secretos, credenciales ni datos sensibles innecesarios.

## 4. Memoria de prevención y reutilización

El Gabinete mantiene tres niveles:

- **Índice de incidentes:** inventario consultable por síntoma, causa, proyecto, agente y estado.
- **Reglas aprendidas:** controles generales derivados de incidentes verificados, sin duplicar expedientes.
- **Pruebas de no recurrencia:** tests o verificaciones que detectan el patrón antes de que llegue al usuario.

Antes de iniciar una tarea, cada agente debe consultar las reglas aprendidas y los incidentes pertinentes a su tarea, proyecto, herramientas y tipo de operación. Si ya existe una solución documentada, debe reutilizarla y citar el expediente; no volver a pedir al usuario que explique o investigue lo mismo.

Cuando un agente encuentre un fallo ya documentado, debe aplicar la solución existente y añadir evidencia de la nueva ocurrencia al expediente, en lugar de abrir una investigación duplicada, salvo que existan diferencias relevantes.

## 5. Responsabilidad y límites

- El agente que produjo el error lidera la investigación; un segundo agente puede auditarla.
- El agente auditor debe cuestionar la causa raíz y comprobar que la prevención realmente cubre el fallo.
- No se permite cerrar un incidente solo porque el resultado visible fue corregido.
- No se permite convertir una hipótesis de causa raíz en hecho sin evidencia.
- No se permite declarar que se ejecutó, probó, guardó, desplegó o notificó algo si no existe evidencia verificable.
- Si el fallo depende de una limitación externa o de permisos, el agente debe identificar el límite exacto, probar alternativas autorizadas y documentar el bloqueo residual.
- Si la corrección requiere autorización del usuario o afecta una zona protegida, preparar el cambio sin ejecutarlo y explicar únicamente la autorización concreta que falta.
- El usuario no es el mecanismo de QA, memoria, diagnóstico ni distribución del aprendizaje.

## 6. Criterio de cierre

Un incidente solo alcanza VERIFICADO cuando:
1. La causa raíz está sustentada por evidencia.
2. El resultado afectado está corregido o su impacto está delimitado.
3. Existe prevención reutilizable.
4. Una prueba de regresión o comprobación equivalente pasó.
5. El aprendizaje quedó en el Gabinete y los agentes pertinentes recibieron la notificación.

Si falta cualquiera de estos puntos, el incidente permanece abierto con su bloqueo explícito.

## 7. Integración con el protocolo de continuidad y el bus

Cada incidente y cada regla aprendida deben poder referenciarse desde el estado global, el diario de eventos y el bus. Los eventos deben incluir `incident_id`, `project_ids`, `source_agent`, `root_cause_status`, `prevention_ref` y `verification_status` cuando aplique.

El Gabinete es la memoria operativa transversal de aprendizaje. No sustituye el historial técnico de cada proyecto ni los archivos canónicos. Steambox queda reservado al ámbito del motor U6 y no se usa como ubicación de este contrato general.

## 8. Regla para el usuario

No volver a pedir al usuario que encuentre por nosotros dónde fallamos cuando la evidencia está en los repositorios, archivos, logs, trazas, herramientas o historial disponible. Primero investigar y reconstruir. Preguntar solo si existe un dato imprescindible al que ningún agente ni herramienta autorizada tenga acceso, después de documentar qué se buscó y qué falta.
