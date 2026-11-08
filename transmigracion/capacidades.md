# Capacidades

Inventario de lo que el agente puede hacer y con qué herramienta real
lo hace. Esto es lo que se clona. Cada capacidad dice dónde vive, cómo
se corre y qué no puede.

## Coordinar entre modelos

- **Tablero + protocolo callback** (CAPCOT
  `ajustes_entre_modelos/DELEGACIONES.md` y `PROTOCOLO_CALLBACK.md`):
  el repo hace de bus entre modelos; el agente es el router que revisa
  el tablero y avisa qué está atorado. El motor U6 es un proyecto
  aparte y no lleva delegaciones en ese tablero.
- **Aviso callback** (workflow `callback-aviso.yml`, listo en
  `~/workspace/callback-aviso/`, sin subir): al cambiar el tablero y
  cada hora, abre un issue con etiqueta `callback` por cada delegación
  pendiente. Necesita el agente de código de Copilot activo en
  Settings > Copilot.

## Orquestar

- **Orquestador** (`orquestador/orquestador.py`): lee el tablero y el
  protocolo, se los pasa a `openai/gpt-oss-120b` por Groq (API
  gratuita) y escribe un reporte de qué está atorado. No gasta tokens
  del modelo caro. Workflow `orquestador.yml` listo en
  `~/workspace/orquestador-workflow/` (corre diario 07:00 CDMX +
  dispatch; va por navegador; necesita el secreto GROQ_API_KEY).

## Leer lo que no se puede leer

- **Puente de lectura** (`puente-lectura/leer.py`): trae el texto por
  varias rutas (raw de GitHub, API de GitHub, lectura directa), lo
  leen Gemini y Groq, y Gemini une las dos lecturas en una nota
  marcando discrepancias. Trunca a 12.000 caracteres por el límite de
  8.000 TPM de Groq. Uso: `python3 leer.py <URL> [--salida ARCHIVO]`.

## Hablar con Groq sin clave

- **Puente Groq** (`puente-groq/proxy.py`): proxy local en
  `http://127.0.0.1:8080/v1` que reenvía a Groq. La clave la resuelve
  el conector, nunca sale de la bóveda. Si la máquina se reemplaza,
  hay que relanzarlo.

## Agente de código a costo cero

- **DeepSeek Harness** (`dsh/`): el loop es configurable y acepta
  cualquier endpoint OpenAI-compatible. Con el puente Groq funciona,
  pero el tier gratis de Groq tiene 8.000 TPM y el prompt de dsh pesa
  ~4.600 tokens: la segunda llamada da 429. Ver `dsh/DSH_PRUEBA_HUMO.md`.
- **Free Claude Code** (no instalado): proxy local que enruta a 61
  proveedores y reintenta solo ante 429/500. Es la pieza que falta
  delante de dsh. Licencia por verificar (el puente la leyó como AGPL
  v3; la investigación anterior decía MIT).
- **LiteLLM** (no instalado): solo APIs gratuitas, con fallbacks y
  cooldowns. Alternativa a Free Claude Code.

## Narrar en español

- **Kit TTS** (CAPCOT `tools/tts/`): `narrate.py` (edge-tts, voz
  es-MX-JorgeNeural) y `narrate_piper.py` (fallback offline, voz
  es_MX-ald-medium). edge-tts está bloqueado en la VM de Pecas; Piper
  sí funciona. La voz JorgeNeural queda en Imaginantes y en el box.

## Buscar en el código

- **codebase-memory-mcp**: índice del código de CAPCOT (12.129 nodos)
  y del motor U6 (13.531 nodos). El índice es foto del 2026-11-07:
  hay que re-indexar cuando los repos cambien.

## Relevo y auto-escala

- **Relevo** (baterias-tokens `RELEVO.md` + workflow `relevo.yml`,
  listo en `~/workspace/agente-cero-costo-cableado/`, sin subir):
  cuando el agente se queda sin tokens crea `RELEVO_ACTIVO` y
  gpt-oss-120b toma el tablero en Actions cada hora. El relevo no
  puede: navegador/Studio, iniciar sesión, crear repos, correr lo del
  box.
- **Escala** (workflow `escala.yml`, mismo lugar, sin subir): revisa
  diario el tamaño de los repos del stack y si alguno pasa 800 MB abre
  un issue con etiqueta `escala`.
- **Máquina en el repo** (`maquina/`): Dockerfile + setup.sh que
  convierten cualquier host (Docker o VM limpia, p. ej. Oracle ARM) en
  la máquina agente. Sin Docker en la VM de Pecas: la imagen no está
  probada.

## Modelos locales

- **TwIL-8B** (`modelos/TWIL-8B.md`): 8.79B parámetros, contexto
  131k, licencia no comercial. Necesita ~10 GB de RAM en uso: no cabe
  en la VM de Pecas (7.7 GB). El análogo a costo cero es Oracle Always
  Free ARM (4 vCPU, 24 GB RAM), sin crear.
- **Swap** (`memoria/swap.md`): la VM no puede agregar memoria
  virtual; el contenedor bloquea `swapon`. Un repo es almacenamiento,
  no RAM.

## Límites del agente

- No monta el MP4 final ni publica: el montaje oficial, QA y
  programación son de Imaginantes con voz es-MX-JorgeNeural.
- No edita `data/horario_*.json`, `data/publicaciones.json` ni
  `data/rotacion.json` de CAPCOT.
- No toca el motor U6 desde CAPCOT: Engine V5 y el catálogo 244 son
  la referencia fija.
- No sube workflows por API: la app de GitHub no tiene permiso
  Workflows; van por navegador con la cuenta del usuario.
