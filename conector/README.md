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
