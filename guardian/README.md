# Guardián

Vigilante del stack agente-cero-costo / CAPCOT / Motor U6. Está pendiente de
errores y los repara solo.

## Regla primera: trabaja sin Marco. No espera. Solo escala lo imposible.

El sistema **NO puede depender de que Marco esté despierto o presente**. Si
hay que hacer cosas y él está dormido, no se espera a que él las entregue.
Ayer (2026-11-08) y varias veces él no fue a trabajar porque se quedó atorado
autorizando cosas que los modelos debían hacer solos — para eso les dio las
indicaciones, como usar la computadora y usar sus claves para hacerlo.

Por eso el guardián:

- **Actúa solo** con los accesos que ya existen (la app de GitHub, el
  `GITHUB_TOKEN` de Actions, los conectores, la bóveda). No pide
  autorización, no espera a que Marco despierte, no deja tareas en pausa
  esperando su confirmación.
- **Usa las claves guardadas**: si un paso necesita una clave o acceso que ya
  está guardado (secreto de Actions, conector, bóveda), lo usa; no lo pide
  de nuevo.
- **Solo escala lo literalmente imposible sin él**: una contraseña que solo
  él conoce, una confirmación que solo él puede dar en su propia cuenta, o
  hablarle a Grok en su chat porque el bus no lo despierta. Eso se marca
  `NECESITA_MARCO` con la causa en una línea. Nada más llega a Marco.

## Regla segunda: no inventa reglas. Lee y hace cumplir las que ya existen.

El guardián **NO crea un sistema paralelo**. Cada chequeo cita el contrato
o skill que hace cumplir. Si un caso no está cubierto por ningún contrato,
lo marca como `HUECO_CONTRATO` (qué regla falta escribir y en qué
documento), no inventa la regla por su cuenta. Si dos contratos se
contradicen, vale la regla más nueva y específica.

### Contratos que lee y qué hace cumplir de cada uno

| Contrato | Qué hace cumplir el guardián | Chequeo |
|---|---|---|
| CAPCOT `docs/PLAN_MAESTRO_AUTOMATICO.md` (fuente de verdad) | §1: Mj no necesita estar presente, la revisión humana es opcional (base de la regla primera). §4: fallo en una compuerta → reintento máx. 2 → FALLIDO y cápsula de reserva del backlog. §5: compuertas de calidad (fuentes con DOI que resuelve, duración 60–90 s, 1080×1920 30 fps, −14 LUFS ±1). | D, E |
| CAPCOT `ajustes_entre_modelos/PROTOCOLO_CALLBACK.md` | Regla 1: delegar sin escribirla en DELEGACIONES.md es no delegar. Regla 3: HECHA con evidencia (commit, enlace, archivo); sin evidencia no está hecha. Regla 4: si el receptor no puede, marca BLOQUEADA con el motivo. Regla 5: más de un día en PENDIENTE → Pecas lo reporta (de aquí sale el umbral de 24 h). El aviso es el workflow `callback-aviso.yml` (Issue con etiqueta `callback`); el tablero por sí solo no despierta a nadie. Pecas es el router. | A, B, G |
| CAPCOT `ajustes_entre_modelos/COORDINACION_CHATGPT_IMAGINANTES.md` | Regla de oro: no inventar datos, fuentes ni DOIs. §3: entrega en `cola/entrada/<id>/` (storyboard, frames 9:16, fuentes.md, ESTADO_EJECUCION.md); solo texto en commits; **no subir mp4/token; si los frames no pueden ir al repo, indicar en ESTADO_EJECUCION.md dónde están**. §4: prohibido (otra serie, otra voz, publicar, inventar DOIs, editar `data/*.json`, tocar el motor U6). §6: máx 3/día, 6 slots, Imaginantes decide. §7: Imaginantes toma el paquete con `procesar_cola.py` → `montar_capsula.py` (JorgeNeural) → `qa_capsula.py` (obligatoria) → `publicar.py`. | C, E, G |
| CAPCOT `docs/LINEA_EDITORIAL_VISUAL.json` v1.2 | valores_fijos: 9:16, 1080×1920, 30 fps, 60–95 s (objetivo 75–90), 6 escenas de ~10 s, −14 LUFS, voz oficial es-MX-JorgeNeural +7%/−2Hz, cierre "Esto fue Datos y ociosidades.", cortinilla de fuentes 6 s. revision_diaria: por lo menos una vez al día; **si Imaginantes deja de publicar, el relevo es automático** al detectar que no hubo publicación. | E |
| Skill `capcot-qa` | **Puertas duras**: duración real a ±5 s del `target_duration_seconds` del storyboard; voz rechazada (Piper es_MX-ald-medium, es_ES-sharvard-medium, es_MX-claude-high) = NO PASA; huecos largos de silencio = NO PASA. **No existe "PASA como borrador"** cuando una puerta dura falla. | G (contradicciones) |
| Skill `capcot-narracion` | Voz oficial es-MX-JorgeNeural (edge-tts +7%/−2Hz); voz local Kokoro-82M (em_alex, em_santa, ef_dora); **NO uses Piper**; voz oficial por Actions: workflow `edge-tts-voz.yml`. | G |
| Skill `capcot-montaje` | Salida `capsula.mp4` 1080×1920 9:16 30 fps, 60–95 s, −14 LUFS, subtítulos, cortinilla 6 s, cierre. El montaje oficial lo hace Imaginantes; esta skill hace borradores. | E |
| Skill `capcot-frames` | Una imagen por escena, 9:16, sin texto dentro de la imagen; el `image_prompt` se usa tal cual. | C, G |
| Skill `capcot-guion` | Formato del `storyboard.json`; regla de oro: no inventar datos, fuentes ni DOIs; cada afirmación con fuente real en `sources` y `source_ids`. | C |
| Skill `microseries-guion` (§17) | QA con puertas duras adaptado de capcot-qa: duración medida (no estimada), voz = lock, consistencia del personaje = puerta dura; no existe "PASA como borrador". | G |
| Skill `trabajar-con-marco` | Nunca "no se puede" sin probar el análogo/fallback y dejar el intento en el repo; cuando no se puede aquí, decir dónde sí se puede; resolver sin preguntar; verificar en el repo antes de decir que está hecho. | D |
| agente-cero-costo `conector/ESTADO.md` + `conector/bus/` + bloque `[EMITIR]` | El bus es un buzón, no una llamada. El estado vigente es el del evento más nuevo del bus. | A, F |
| Motor U6 | **Prohibido tocar Engine V5 y el catálogo 244.** El guardián solo reporta su estado si hace falta; no lo repara. | — |

### Huecos y contradicciones ya detectados (chequeo G)

- **G1**: `LINEA_EDITORIAL_VISUAL.json` `valores_fijos.voz_fallback` dice "es_MX-ald-medium (Piper, offline)", pero `capcot-narracion` dice "NO uses Piper" y `capcot-qa` la marca puerta dura. El JSON canónico está desactualizado; vale la regla más nueva (Kokoro local / JorgeNeural por Actions).
- **G2**: `trabajar-con-marco/SKILL.md` dice "el fallback es Piper offline" (línea vieja, anterior a 2026-11-08). Hay que corregirla en la skill.
- **G3**: `DELEGACIONES.md` tiene delegaciones dirigidas PARA: Marco (subir workflows por navegador, activar seguridad manual, crear cuenta Clayzo). Marco NO es el autorizador (corrección 2026-11-08 16:27): hay que reasignarlas a Copilot/Codex por el bus.
- **G4**: `capcot-frames/SKILL.md` dice de explainroo "NO instalado, NO probado"; se probó el 2026-11-09 con Barreleye (da diagrama vectorial, no lápiz; no se adopta como reemplazo de frames). La skill está desactualizada.
- **G5**: `PROTOCOLO_CALLBACK.md` dice que `callback-aviso.yml` está "listo para subirlo por navegador con la cuenta de Marco" (regla vieja). La vía es delegar la subida a Copilot/Codex por el bus.

## Verificación real, no por intento (regla dura)

Cada chequeo lee el **ESTADO REAL actual**, no el intento. El archivo existe
y tiene el contenido esperado, el workflow corrió en verde, el PR está
abierto, el video está publicado, el Issue existe, el ESTADO.md tiene la
versión que dice tener. **Nunca se infiere "ya está" por haberlo intentado.**

- **Encontrar una inconsistencia NO es prueba de que está hecho: es prueba
  de que NO está hecho**, y se reporta como fallo con la evidencia (qué se
  esperaba, qué hay realmente).
- **Prohibido el "ya está" por intento**: si el guardián intentó reparar
  algo y no puede verificar el resultado en el estado real, lo marca como
  `NO_VERIFICADO`, no como hecho.
- **Si el estado no se puede leer, tampoco se da por verde**: se marca
  `NO_VERIFICADO` con el motivo (p. ej. el repo es privado para este token),
  no se omite en silencio.

Esto evita lo que ya pasó:

| Lo que se dijo | Lo que había en el estado real |
|---|---|
| El estado v8 "emitido" | `ESTADO.md` sigue en v7 (2026-11-08 16:28); el evento v8 sí está en `conector/bus/` |
| Delegaciones "enviadas" (#9, #11, #14) | Siguen abiertas sin respuesta; nadie las tomó |
| Workflows "delegados" a Copilot/Codex (v7+v8) | Nunca se subieron: CAPCOT no tiene `.github/workflows/` en main |
| La cápsula "programada" (la rana, 2026-11-09 07:00) | Nunca salió en TikTok; el slot se perdió |
| El PR de los arreglos del gestor "listo" | La rama existe con los arreglos, pero el PR nunca se abrió (la automatización solo muestra el formulario) |

### Qué lee cada chequeo como estado real, y cómo se verifica cada reparación

| Chequeo | Estado real que lee | Cómo se verifica la reparación |
|---|---|---|
| A. Delegaciones | Issues `[BUS]` abiertos por API + si existe un Issue `[BUS] hecho` o un PR que los mencione (así se descubrió que el #9 sí fue respondido por el PR #10) | El Issue de rellamado nuevo se confirma con `GET /issues/{n}`; si no se confirma, `NO_VERIFICADO` |
| B. Ramas sin PR | Ramas por API + PRs abiertos (cabeza y base) | El PR nuevo se confirma con `GET /pulls?head=...`; si no se confirma, `NO_VERIFICADO` |
| C. Sobrepeso | Árbol de CAPCOT main por API (qué hay en `frames/`) | El Issue `[BUS]` a Grok se confirma con `GET /issues/{n}`; el archivo de evento en `conector/bus/` NO es el Issue y no cuenta como reparado |
| D. Workflows | Runs con `failure` por API en los 3 repos | No repara solo: clasifica y propone el parche; la verificación es el siguiente run en verde |
| E. Slots | Árbol de CAPCOT main por API (paquetes con slot pasado y sin MP4) | No repara solo: marca ATORADO; la verificación es que el MP4 aparezca en el repo |
| F. Estado del bus | `estado.json` y el directorio `conector/bus/` por API | Los archivos regenerados se verifican por relectura local; el estado en main solo queda verificado cuando el workflow haga commit/push y la próxima corrida lo lea |
| G. Huecos | Los contratos mismos, leídos de main y de las skills locales | No repara: marca `HUECO_CONTRATO`; la verificación es que el documento se corrija |

### Límite honesto: verificación entre repos

Con el `GITHUB_TOKEN` por defecto de Actions, el guardián solo puede leer
y escribir **su propio repo** (agente-cero-costo). Los workflows y árboles
de CAPCOT y del motor se leen por API pública mientras sean públicos; si un
repo es privado para ese token, el chequeo marca `NO_VERIFICADO` en vez de
dar por verde. El guardián **no pide claves nuevas**: reporta la limitación
y la próxima corrida con acceso la verifica. (Verificado 2026-11-09:
`motor-u6-storage` devuelve 404 a la API anónima; sus runs no se pueden
verificar desde fuera.)

## Por qué existe (las dos causas raíz que lo motivaron, 2026-11-09)

**1. Las llamadas a Grok no se hacen.** El bus es un buzón, no una llamada:
guarda el mensaje pero no despierta a ningún modelo (lo dice el propio Issue
#14). Grok solo lee el bus cuando sus Automations corren (C1 ~11:00, C3
~18:00, C2 ~20:00 CST, si siguen activas) o cuando Marco le habla en su chat.
Los pedidos que se dejan en `cola/entrada/` o `handoffs/grok_inbox/` sin
Issue `[BUS]` nunca llegan (caso ASTRA, 2026-11-09 18:40). El workflow viejo
`capcot-grok-dispatch.yml` no está en main, dispara solo con `*.json` (los
paquetes son carpetas) y todas sus corridas del 1-nov fallaron por falta de
`GROK_WEBHOOK_URL` (webhook Firebase abandonado). El orquestador nunca corre
porque `orquestador.yml` nunca se subió a CAPCOT (no hay `.github/workflows/`
en main). Y las delegaciones v7/v8 a Copilot/Codex para subir los workflows
nunca se cumplieron: en agente-cero-costo solo están
`github-native-agent-bus.yml` y `unified-agent-bus.yml`; en CAPCOT no hay
ninguno. Además el `ESTADO.md` de main sigue en v7 (2026-11-08 16:28) aunque
el evento v8 sí quedó en `conector/bus/`: el foquito muestra la delegación
vieja. Los Issues #9, #11 y #14 siguen abiertos sin respuesta.

**2. Lo que Grok hizo "se murió porque está muy grande en peso".** Los 9
frames de ASTRA (1080×1920 PNG, generados en el chat de Grok el 2026-11-09
22:29–22:30) nunca llegaron al repo: `frames/` solo tiene README. La subida
binaria falló por el límite del conector. Los límites SÍ están marcados (ver
tabla abajo): el push por conector rechaza binarios por completo y el snapshot
es máx 16 MiB UTF-8. La receta de arreglo (JPEG calidad 85, lotes < 10 MiB)
está propuesta en el Issue #18 desde el 2026-11-09 22:38, pero nadie la
ejecutó. Y el PR de los arreglos del gestor (rama
`grok-arreglos-gestor-20261109`, con todos los arreglos aplicados) nunca se
abrió: la automatización de Grok solo muestra el formulario, no lo envía.

## Qué vigila (chequeos)

| Chequeo | Fuente (contrato que hace cumplir) | Regla | Reparación sola |
|---|---|---|---|
| A. Delegaciones sin respuesta | PROTOCOLO_CALLBACK regla 5 (más de un día en PENDIENTE → Pecas lo reporta) + bus [EMITIR] | Issue `[BUS] indicacion` abierto > 24 h sin hecho/PR/rama | Re-emite como Issue nuevo (RELLAMADO n/3). Tras 3 rellamados: `NECESITA_MARCO` (solo un humano en el chat de Grok lo despierta) |
| B. Ramas sin PR | PROTOCOLO_CALLBACK regla 3 (HECHA con evidencia; sin evidencia no está hecha) | Rama con commit < 7 días y sin PR abierto | **Abre el PR (sin merge)** con `gh` — el guardián sí puede, corre en Actions con `GITHUB_TOKEN` |
| C. Entregas con sobrepeso | COORDINACION §3 (no subir mp4/token; si los frames no pueden ir al repo, indicar en ESTADO_EJECUCION.md dónde están) + límites del push por conector | `frames/` vacío > 12 h, o archivo > 16 MiB | Emite Issue `[BUS]` a Grok con la receta exacta (JPEG q85, lotes < 10 MiB). No puede convertir lo que está en el chat de Grok, no en el repo |
| D. Workflows fallidos | PLAN_MAESTRO §4 (fallo → reintento máx. 2 → FALLIDO y cápsula de reserva) + trabajar-con-marco (nunca "no se puede" sin análogo) | Runs con `failure` en las últimas 24 h (3 repos) | Clasifica la causa (YAML, secreto, test) y propone el parche en el reporte |
| E. Slots perdidos | LINEA_EDITORIAL_VISUAL.json revision_diaria (relevo automático al detectar que no hubo publicación) + COORDINACION §6 | Paquete con slot pasado y sin MP4 | Lo marca ATORADO en el reporte para la revisión diaria (no remonta: eso es de Imaginantes o de un relevo con clips) |
| F. Estado desactualizado | bus (conector/ESTADO.md es el tablero vigente) | `estado.json` con versión menor que el evento más nuevo del bus | Regenera `estado.json`/`ESTADO.md` desde el evento nuevo (su propio repo) |
| G. Huecos en el contrato | Los propios contratos (CONTRATOS en `guardian.py`) | Caso sin regla, o dos contratos que se contradicen | **No repara inventando la regla**: marca `HUECO_CONTRATO` con qué documento hay que escribir o corregir. Los huecos ya detectados están listados arriba (G1–G5) |

## Cómo corre

- **GitHub Actions**: workflow `guardian.yml`, cada 6 horas (00:17, 06:17,
  12:17, 18:17 CST aprox.) + `workflow_dispatch` a mano. Necesita solo el
  `GITHUB_TOKEN` automático; no pide secretos nuevos.
- **Local (prueba de Pecas)**: `python3 guardian/guardian.py --check --skills-dir ~/workspace/custom-skills` (solo lectura; sin `--skills-dir` los huecos G2/G4 quedan como no verificados) o `--repair` (aplica reparaciones; sin `gh` autenticado deja los
  rellamados listos en `guardian/reemision-pendiente-*.md`).
- **Salida**: cada corrida deja `guardian/reporte-YYYY-MM-DD-HHMM.md` y
  actualiza `guardian/estado.json` (contador de rellamados, última corrida).
  Cuando repara algo, deja el evento en `conector/bus/`.

## Qué NO hace

No publica, no hace merge, no toca Engine V5 ni el catálogo 244 del motor,
no pide claves nuevas, no instala nada, no espera a Marco.

## Límites exactos que usa

| Límite | Valor | Dónde está marcado |
|---|---|---|
| Delegación sin respuesta → rellamado | 24 h | PROTOCOLO_CALLBACK regla 5 ("más de un día en PENDIENTE") — el guardián solo la hace cumplir, no la inventó |
| Rellamados antes de escalar a Marco | 3 | `guardian.py` (`MAX_RELLAMADOS`) |
| Snapshot por conector (Muse push-files) | máx 16 MiB UTF-8, **0 bytes binarios**, máx 2000 archivos, manifiesto 1 MiB | `github/references/snapshot-push.md` |
| Lote seguro para binarios | < 10 MiB por lote, < 5 MiB por archivo | `guardian.py` |
| Archivo único por API de GitHub | 100 MB (el conector igual rechaza binarios) | docs de GitHub |
| Ventana de fallos de Actions | últimas 24 h | `guardian.py` |
| Paquete con `frames/` vacío → ATORADO_PESO | > 12 h | `guardian.py` |
| Mensaje de Telegram (referencia) | 4096 caracteres | `bot/gestor.py` (`TG_LIMITE`) |
| Automations de Grok en grok.com | C1 ~11:00, C3 ~18:00, C2 ~20:00 CST (sin verificar si siguen activas) | `docs/SCRIPT_AUTOMATIONS_GROK_CAPCOT.md` |

## Instalación (para Copilot/Codex por el bus)

1. `guardian/guardian.py` y `guardian/README.md` van a `guardian/` en
   `marcojpad-hash/agente-cero-costo` (texto, los sube Pecas por push-files).
2. `.github/workflows/guardian.yml` va a `.github/workflows/` del mismo repo
   (lo sube Copilot/Codex: la app de Muse no tiene permiso Workflows).
3. Al terminar, dejar un evento hecho en el bus con los links.
