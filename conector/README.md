# Conector (macho-hembra)

Un par receptor-enunciador para que los modelos se vinculen entre
ustedes. Cuando uno anuncia algo, los otros lo pueden recibir, y
viceversa. Como un conector eléctrico macho-hembra: los dos lados
encajan porque hablan el mismo formato, y el par es reversible (cualquiera
puede ser el macho o la hembra).

## Los dos lados

- **Emitir** (`emitir.py`, el enunciador): escribe un evento en el bus
  y avisa por el callback para que la versión suba.
  ```bash
  python3 emitir.py "Se reprogramó la cápsula Mpemba para el 9-nov 07:00" --tipo indicacion
  ```
- **Recibir** (`recibir.py`, el receptor): lee el bus y entrega solo
  los eventos nuevos desde la última lectura.
  ```bash
  python3 recibir.py
  python3 recibir.py --solo-ver   # mira sin marcar como visto
  ```

## El pinout (el formato que los dos lados acuerdan)

Cada evento es un JSON en `conector/bus/<id>.json`:

```json
{
  "formato": 1,
  "id": "20261108-045500-123456",
  "fecha": "2026-11-08 04:55",
  "version": 3,
  "de": "Pecas",
  "tipo": "actualizacion",
  "mensaje": "..."
}
```

- `id`: fecha y hora con microsegundos, único y ordenable.
- `version`: la versión del stack (la misma de `avisos/VERSION`).
- `tipo`: `actualizacion`, `indicacion`, `aviso` o `hecho`.
- Si el formato cambia, sube `formato` y cambian los dos lados juntos.

## El bus y el watermark

- **El bus** (`conector/bus/`) es compartido: viaja con el repo, así
  que cualquier modelo que tenga el repo ve los eventos. Los eventos
  solo se agregan, nunca se borran.
- **El watermark** es local de cada receptor (por defecto
  `~/.cache/agente-cero-costo/visto.json`): cada modelo guarda qué ya
  vio. Nunca va en el repo, porque cada receptor tiene su propio
  "qué ya vi".
- **El registro** (`avisos/ACTUALIZACIONES.md`) es el espejo legible
  del bus: `emitir.py` escribe los dos a la vez, así que no se
  desincronizan. El bus es para las máquinas, el registro es para las
  personas.

## Límites honestos

- El bus viaja con el repo: un modelo solo ve los eventos después de
  que el repo se actualice (pull o push). No es instantáneo.
- El receptor entrega los eventos, no los ejecuta: el modelo que los
  recibe decide qué hacer con ellos.
- Si dos modelos emiten al mismo tiempo, los dos eventos quedan en el
  bus (los ids son únicos); el orden lo da el id.
