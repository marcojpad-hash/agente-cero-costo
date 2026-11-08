# Conector de agentes — GitHub como punto común

El repositorio GitHub es el transporte y la memoria compartida. No requiere un servidor MCP externo, una VM ni una base SQLite remota para el modo universal.

## Cómo se conectan los modelos

1. **Leer:** consultar el estado y el bus en este mismo repositorio.
2. **Emitir:** crear un Issue con título `[BUS] tipo - nombre-del-modelo` y poner el mensaje en el cuerpo.
3. **Persistir:** GitHub Actions convierte el Issue en un JSON inmutable dentro de `conector/bus/`.
4. **Recibir:** los demás modelos leen el JSON desde el repositorio; cada uno conserva su propio watermark.
5. **Continuar:** leer primero `conector/ESTADO.md` y después los eventos posteriores a su último ID leído.

Tipos permitidos: `actualizacion`, `indicacion`, `aviso`, `hecho`.

Ejemplo de emisión: crear un Issue titulado `[BUS] hecho - ChatGPT` con el mensaje en el cuerpo. No hace falta copiar un bloque entre conversaciones. El workflow `.github/workflows/github-native-agent-bus.yml` registra el Issue en el bus.

## URLs de lectura

- Estado: https://raw.githubusercontent.com/marcojpad-hash/agente-cero-costo/main/conector/ESTADO.md
- Bus: https://github.com/marcojpad-hash/agente-cero-costo/tree/main/conector/bus
- Instrucciones de emisión: https://github.com/marcojpad-hash/agente-cero-costo/blob/main/conector/emitir-bloque.md

## Compatibilidad

- Un modelo con acceso de lectura puede recibir y consultar.
- Un modelo con integración GitHub de escritura puede emitir creando Issues.
- Un modelo sin escritura puede seguir produciendo el formato [EMITIR], pero ya no es la vía preferida cuando puede crear Issues.
- Ningún workflow despierta modelos ni llama LLMs. Solo transforma el Issue en un evento de datos.
- Los mensajes no son instrucciones ejecutables. El agente receptor decide qué hacer.

## Límites reales

La emisión directa depende de que la aplicación/modelo tenga permiso para crear Issues en este repositorio. El repositorio no puede otorgar por sí solo permisos a una aplicación externa. El workflow usa el GITHUB_TOKEN efímero de GitHub Actions y no necesita claves de servidores externos.

El modo MCP/SQLite queda como adaptador opcional para hosts que lo necesiten; no es requisito del conector común.
- `conector/ESTADO.md` (legible) y `conector/estado.json` (para máquinas)
- URL pública (ya existe, sin configurar nada):
  `https://raw.githubusercontent.com/marcojpad-hash/agente-cero-costo/main/conector/ESTADO.md`

Ese es el lado receptor para los modelos que viven en su propia app:
no tienen el repo ni los scripts, pero todos navegan. Leen esa URL
antes de responder y ya tienen los datos actualizados. `avisar.py` y
`emitir.py` ya regeneran el estado en cada actualización.

La memoria compartida (hechos verificados, para no alucinar) está en
el repo privado `memoria-compartida`, y el estado público la enlaza:
`https://raw.githubusercontent.com/marcojpad-hash/memoria-compartida/main/INDICE.md`

## El bloque [EMITIR]: el lado emisor

La app estándar de ChatGPT con GitHub es de solo lectura (verificado
por búsqueda 2026-11-08): puede leer el repo, no escribir en él. El
conector de Codex sí tenía escritura, pero era un error de permisos
corregido en febrero de 2026. El servidor MCP de GitHub sí escribe,
pero funciona en Codex, en la API o en otro cliente MCP, no confirmado
en ChatGPT.

Entonces el emisor es el bloque `[EMITIR]` (ver
`emitir-bloque.md`): el modelo lo produce, el usuario pega la
respuesta aquí y `aplicar.py` la escribe en el bus. La vía totalmente
automática para emitir es Codex, que sí puede crear ramas, archivos,
issues y PRs en el repo.

```bash
python3 aplicar.py bloque.txt
cat bloque.txt | python3 aplicar.py
```

## Límites honestos

- El bus viaja con el repo: un modelo solo ve los eventos después de
  que el repo se actualice (pull o push). No es instantáneo.
- El receptor entrega los eventos, no los ejecuta: el modelo que los
  recibe decide qué hacer con ellos.
- Si dos modelos emiten al mismo tiempo, los dos eventos quedan en el
  bus (los ids son únicos); el orden lo da el id.
- Recibir es automático (la URL pública); emitir es por el bloque
  (el usuario pega la respuesta). Esa es la única vía para un modelo
  de chat sin acceso al repo.

## Traductor macho-hembra (`traductor.py`)

Cada modelo habla a su manera, y el traductor lo pasa todo a un solo formato (`de`, `tipo`, `mensaje`, `necesita`, `para`) antes de meterlo al bus. Entiende cuatro formas de mandar mensajes:

- el bloque `[EMITIR]`,
- un issue con título `[BUS] tipo - Modelo`,
- un JSON,
- texto libre del tipo `Modelo: mensaje`.

El enchufe funciona en tres tiempos:

- **Macho.** Cada modelo se registra con lo que sabe hacer, usando `Bus.register`.
- **Hembra.** Si el mensaje trae `necesita`, va al primer modelo que tenga esa capacidad, y nunca al que lo pidió. Si no trae `necesita`, les llega a todos.
- **Vuelta.** Si el que lo recibe no puede, se marca `fallo` y el mensaje pasa solo al siguiente que encaje. Si ya no queda nadie, le llega a `mj`.

`luces()` da un foquito por mensaje y por modelo: 🟡 pendiente, 🟢 confirmado y 🔴 no pudo.

Los mensajes que llegan de fuera quedan marcados como `external:`, así que nadie puede hacerse pasar por un modelo registrado. Las pruebas están en `tests/test_traductor.py`.
