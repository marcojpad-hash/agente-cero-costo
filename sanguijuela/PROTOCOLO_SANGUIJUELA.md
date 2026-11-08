# Protocolo sanguijuela

## La idea

El que orquesta no gasta sus tokens. El trabajo pesado (razonar,
generar, resolver) lo hacen los modelos gratuitos, con sus tokens, y
las herramientas que ya existen (sus MCP, sus aplicaciones, sus
cableados). El orquestador solo pone la capa fina: decidir qué hacer,
verificar y unificar. Como una sanguijuela: se alimenta de los otros
sin matarlos. Como una rémora: se pega a lo que ya existe y lo usa,
en vez de reconstruirlo.

Esto funciona porque todos los modelos son el mismo por la
transmigración: no importa quién esté orquestando en turno, es el
mismo sistema con la misma información. El que orquesta es el mismo;
los que generan son los gratuitos.

## Reglas

1. **El orquestador no genera.** No escribe el texto largo, no genera
   el código, no razona el problema completo. Escribe el encargo corto
   y lo manda al modelo que corresponde.
2. **El orquestador solo gasta en la capa fina:** decidir, verificar,
   unificar. Nada más.
3. **La rémora:** antes de construir una herramienta, usar la que ya
   existe. Los MCP, los CLIs y los scripts del stack son de todos:
   codebase-memory-mcp para buscar en el código, el puente-lectura
   para leer lo que no se abre, el puente Groq para hablar sin clave,
   dsh para ejecutar. No se reconstruye lo que ya está cableado.
4. **El que genera, genera con sus tokens.** Cada encargo va al modelo
   gratuito que corresponde según la tabla. Si un modelo falla (429,
   413), el encargo pasa al siguiente, sin que el orquestador lo haga
   él mismo.
5. **Contabilidad honesta.** Cada encargo deja constancia: qué modelo
   hizo el trabajo, cuántos tokens aproximados gastó, y qué gastó el
   orquestador (la llamada y la verificación). La sanguijuela no
   elimina el gasto del orquestador, lo reduce a la capa fina.
6. **Si no hay modelo gratuito que lo haga, se dice.** No se finge
   que el orquestador lo hizo gratis: se dice dónde se puede hacer y
   qué cuesta.

## Tabla de enrutado

| Tarea | Quién hace el trabajo pesado | Por qué | Límite |
|---|---|---|---|
| Texto corto, razonamiento, plan | Groq gpt-oss-20b | Rápido, gratis | 8.000 TPM por minuto; encargo + respuesta bajo ~6.000 tokens |
| Texto largo, contexto grande, código largo | Gemini gemini-3-flash-preview | 1M TPM, contexto grande | Límites del nivel gratis no publicados; verificar |
| Leer algo que no se abre | puente-lectura (Gemini + Groq) | Dos arquitecturas, unificadas | Trunca a 12.000 caracteres |
| Ejecutar código, agente | dsh por el puente Groq | El loop funciona | Prompt ~4.600 tokens; la 2ª llamada da 429 |
| Agente con reintentos automáticos | Free Claude Code (no instalado) | Reintenta en 61 proveedores | Necesita Python 3.14; licencia por verificar (AGPL v3 vs MIT) |
| Buscar en el código | codebase-memory-mcp | Indexado | Índice del 2026-11-07; re-indexar si cambia |
| Orquestar, decidir, verificar, unificar | El orquestador (capa fina) | Solo la capa fina | Debe quedarse corto |

## Cómo se usa

`sanguijuela.py` es la sanguijuela en código: recibe el encargo, lo
enruta al modelo gratuito que corresponde y trae el resultado. El
orquestador solo escribe el encargo.

```bash
python3 sanguijuela.py --tipo texto --tarea "resume en 5 puntos..."
python3 sanguijuela.py --tipo texto-largo --tarea "..."
python3 sanguijuela.py --tipo lectura --tarea "https://github.com/..."
python3 sanguijuela.py --tipo codigo --tarea "..." --solo-enrutar
```

`--solo-enrutar` no ejecuta: solo dice a quién le tocaría y con qué
comando. Sirve para planear sin gastar nada.

## Límites honestos

- La sanguijuela reduce el gasto del orquestador, no lo elimina: cada
  encargo cuesta la llamada, la lectura del resultado y la
  verificación. Lo que se ahorra es el trabajo pesado.
- Los modelos gratuitos tienen límites (Groq 8.000 TPM, dsh 429 en la
  2ª llamada). Cuando se acaban, el encargo espera o cambia de modelo;
  no se pasa al modelo caro en silencio.
- La rémora solo funciona con lo que ya está cableado. Los MCP
  pendientes (Firecrawl, por ejemplo) no se pueden usar hasta
  conectarlos.
- El código (tipo `codigo`) se enruta a dsh pero no se ejecuta desde
  aquí: dsh es interactivo y se queda sin TPM en la 2ª llamada. La
  ejecución queda en manual hasta que Free Claude Code o LiteLLM estén
  delante.
