#!/usr/bin/env python3
"""Guardián — vigilante del stack agente-cero-costo / CAPCOT / Motor U6.

PRINCIPIO PRIMERO: Trabaja sin Marco. No espera. Solo escala lo imposible.
- Actúa solo con los accesos que ya existen (GITHUB_TOKEN en Actions, la app
  de GitHub, los conectores). No pide autorización, no espera a que Marco
  despierte, no deja tareas en pausa esperando su confirmación.
- Solo escala a Marco lo que sea literalmente imposible sin él (una
  contraseña que solo él conoce, una confirmación que solo él puede dar en
  su cuenta, o hablarle a Grok en su chat porque el bus no lo despierta).
  Eso se marca NECESITA_MARCO con la causa en una línea.
- Si un paso necesita una clave o acceso ya guardado (secreto de Actions,
  conector, bóveda), lo usa; no lo pide de nuevo.

EL GUARDIÁN NO INVENTA REGLAS. Lee y hace cumplir los contratos y skills
que ya existen; cada chequeo cita su fuente (ver CONTRATOS abajo). Si un
caso no está cubierto por ningún contrato, lo marca como HUECO_CONTRATO
(qué regla falta escribir y en qué documento), no inventa la regla por su
cuenta. Si dos contratos se contradicen, lo marca como contradicción y
vale la regla más nueva y específica (p. ej. capcot-qa 2026-11-08 sobre
cualquier texto anterior que diga que Piper es el fallback).

VERIFICACIÓN REAL, NO POR INTENTO (regla dura).
- Cada chequeo lee el ESTADO REAL actual, no el intento: el archivo existe
  y tiene el contenido esperado, el workflow corrió en verde, el PR está
  abierto, el video está publicado, el Issue existe, el ESTADO.md tiene la
  versión que dice tener. Nunca se infiere "ya está" por haberlo intentado.
- Encontrar una inconsistencia NO es prueba de que está hecho: es prueba
  de que NO está hecho, y se reporta como fallo con la evidencia (qué se
  esperaba, qué hay realmente).
- Prohibido el "ya está" por intento: si el guardián intentó reparar algo
  y no puede verificar el resultado en el estado real, lo marca como
  NO_VERIFICADO, no como hecho.
- Esto evita lo que ya pasó: el estado v8 "emitido" pero ESTADO.md sigue
  en v7; delegaciones "enviadas" que nunca llegaron; workflows "delegados"
  que nunca se subieron; la cápsula "programada" que nunca salió.

Qué vigila (cada chequeo deja su resultado en el reporte y, cuando repara
algo, deja el evento en el bus):
  A. Delegaciones del bus sin respuesta (Grok/Copilot/Codex) > 24 h.
  B. Ramas con trabajo terminado sin PR abierto (el caso del gestor).
  C. Entregas con sobrepeso (frames binarios que no caben en el conector).
  D. Workflows de Actions fallidos en los 3 repos (últimas 24 h).
  E. Cápsulas con slot perdido sin MP4 (cola de CAPCOT).
  F. Estado del bus desactualizado (ESTADO.md viejo con eventos nuevos).
  G. Huecos y contradicciones entre contratos (G1-G5).
  H. Línea editorial en cola/entrada/ (estilo repetido del anterior,
     estilo fuera del catálogo, image_prompt sin "no text").

Modos:
  --check   solo lee y escribe el reporte (no repara nada).
  --repair  además aplica las reparaciones autónomas.
  --repo-root RUTA  checkout local de agente-cero-costo (para probar en la
                    VM de Pecas; si no se da, trabaja solo por API).
  --salida RUTA     dónde escribir el reporte (por defecto, junto al script).

Solo stdlib. No necesita claves de LLM: los chequeos son reglas, no texto
generado. Lecturas por API pública de GitHub (sin token) o con GITHUB_TOKEN
si existe. Escrituras por `gh` (en Actions viene con el token).

Límites exactos que usa (ver README.md, tabla de límites):
  - Delegación sin respuesta: 24 h -> primer rellamado; 3 rellamados -> NECESITA_MARCO.
  - Push por conector (Muse push-files): 16 MiB UTF-8 por snapshot, 0 bytes
    binarios, máx 2000 archivos, manifiesto 1 MiB.
  - Lotes seguros para binarios: cada lote < 10 MiB, cada archivo < 5 MiB,
    JPEG calidad 85 en vez de PNG.
  - Archivo único por API de GitHub: 100 MB (el conector igual rechaza binarios).
  - Ventana de fallos de Actions: últimas 24 h.
  - Paquete sin frames: > 12 h con frames/ vacío -> ATORADO_PESO.
  - Telegram (referencia, no del guardián): mensaje 4096 caracteres.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO_RAIZ = AQUI.parent  # cuando corre dentro del checkout de agente-cero-costo
OWNER = "marcojpad-hash"
REPO_BUS = "agente-cero-costo"
REPOS = [("agente-cero-costo", "agente-cero-costo"),
         ("capcot-capsulas-imaginantes", "CAPCOT"),
         ("motor-u6-storage", "Motor U6")]
API = "https://api.github.com"

# --- Límites exactos (misma tabla que en README.md) ---
LIMITE_DELEGACION_HORAS = 24
MAX_RELLAMADOS = 3
LIMITE_SNAPSHOT_MIB = 16
LIMITE_LOTE_MIB = 10
LIMITE_ARCHIVO_MIB = 5
LIMITE_ARCHIVOS_SNAPSHOT = 2000
VENTANA_FALLOS_HORAS = 24
LIMITE_FRAMES_VACIO_HORAS = 12
NECESITA_MARCO = "NECESITA_MARCO"
HUECO_CONTRATO = "HUECO_CONTRATO"
NO_VERIFICADO = "NO_VERIFICADO"

# --- Contratos y skills que el guardián lee y hace cumplir ---
# Cada chequeo cita su fuente aquí. El guardián NO inventa reglas: si un
# caso no está cubierto, lo marca HUECO_CONTRATO (chequeo G) en vez de
# decidir la regla por su cuenta.
CONTRATOS = {
    "plan_maestro": {
        "ruta": "capcot-capsulas-imaginantes/docs/PLAN_MAESTRO_AUTOMATICO.md",
        "nota": "Fuente de verdad de CAPCOT. Si otro documento lo contradice, manda este.",
        "reglas": [
            "§1: Mj no necesita estar presente; la revisión humana es opcional.",
            "§4: fallo en una compuerta -> reintento máx. 2 -> FALLIDO y se publica una cápsula de reserva del backlog.",
            "§5: compuertas de calidad (fuentes con DOI que resuelve, arco, duración 60-90 s, 1080x1920 30 fps, -14 LUFS ±1, TP <= -1.5 dB, subtítulos <=3 palabras/bloque).",
            "§8: lo que requiere a Mj (una sola vez): OAuth de YouTube, clave de API de imagen, música con licencia.",
        ],
    },
    "protocolo_callback": {
        "ruta": "capcot-capsulas-imaginantes/ajustes_entre_modelos/PROTOCOLO_CALLBACK.md",
        "nota": "Callback entre modelos; el repo hace de bus.",
        "reglas": [
            "Regla 1: toda delegación se escribe en DELEGACIONES.md antes de darla por hecha.",
            "Regla 3: el que termina marca HECHA con evidencia (commit, enlace, archivo). Sin evidencia no está hecha.",
            "Regla 4: si el receptor no puede, marca BLOQUEADA con el motivo. El callback vuelve al que delegó, no se queda en silencio.",
            "Regla 5: si algo lleva más de un día en PENDIENTE sin que nadie lo tome, Pecas lo reporta.",
            "El aviso es el workflow callback-aviso.yml (Issue con etiqueta 'callback' por delegación PENDIENTE a Copilot). El tablero por sí solo no despierta a nadie.",
            "Pecas es el router: revisa el tablero y el correo y avisa qué está atorado.",
        ],
    },
    "coordinacion": {
        "ruta": "capcot-capsulas-imaginantes/ajustes_entre_modelos/COORDINACION_CHATGPT_IMAGINANTES.md",
        "nota": "Documento maestro para modelos externos. Regla de oro: no inventar datos, fuentes ni DOIs.",
        "reglas": [
            "§3 Entrega: cola/entrada/<id>/ con storyboard.json, frames/ (1 imagen por escena 9:16), fuentes.md, ESTADO_EJECUCION.md; solo texto en commits; NO subir mp4/token. Si los frames no pueden ir al repo, indicar en ESTADO_EJECUCION.md dónde están.",
            "§4 Prohibido: estilo litografia_azul_dorado; series distintas a 'Datos y ociosidades'; voz distinta a es-MX-JorgeNeural si alguien monta; publicar; inventar DOIs/cifras/citas/fuentes; editar data/horario_*.json, data/publicaciones.json, data/rotacion.json; tocar el motor U6.",
            "§6 Cupo: máx 3/día; parrilla hasta 6 slots (07:00, 13:30, 14:30, 17:00, 19:00, ~23:30). Imaginantes decide slots.",
            "§7 Imaginantes toma el paquete con procesar_cola.py -> montar_capsula.py (JorgeNeural) -> qa_capsula.py (obligatoria) -> publicar.py. Si falla QA o fuentes, se devuelve con nota en ESTADO_EJECUCION.md, no se publica.",
        ],
    },
    "linea_editorial": {
        "ruta": "capcot-capsulas-imaginantes/docs/LINEA_EDITORIAL_VISUAL.json v1.2.1 (2026-11-10)",
        "nota": "JSON canónico: valores fijos, reglas editoriales, 50 estilos, pipeline de skills, revisión diaria. v1.2.1 corrige el fallback de voz (Kokoro em_santa; Piper PROHIBIDA) y la versión interna.",
        "reglas": [
            "valores_fijos: 9:16, 1080x1920, 30 fps, 60-95 s (objetivo 75-90), 6 escenas de ~10 s, -14 LUFS, voz oficial es-MX-JorgeNeural +7%/-2Hz, voz_fallback Kokoro em_santa speed 0.85 (Piper PROHIBIDA), cierre 'Esto fue Datos y ociosidades.', cortinilla de fuentes 6 s.",
            "reglas_editoriales: un estilo por cápsula del catálogo, NUNCA el de la cápsula anterior; 9:16 con sujeto grande y sin texto dentro de la imagen (el image_prompt siempre termina en 'vertical 9:16, no text'); rigor DATO/INFERENCIA (no se inventan datos, fuentes ni DOIs); la plantilla visual sale del catálogo (prompt_base), no se inventa un estilo nuevo.",
            "Subtítulos oficiales (scripts/montar_capsula.py ass_from_srt + decisión de Marco 2026-11-09): DejaVu Sans 72, negrita, Outline 6, Shadow 2, MarginV 620, blancos sin recuadro.",
            "revision_diaria: por lo menos una vez al día; revisar publicaciones de hoy, cola sin procesar, si Imaginantes publicó o está detenido. Si Imaginantes deja de publicar, el relevo es automático al detectar que no hubo publicación (no espera a que alguien lo pida).",
            "creditos_imaginantes: Imaginantes ya se pausó antes por créditos y la cola se atascó; hay que estar al pendiente.",
        ],
    },
    "capcot_qa": {
        "ruta": "~/workspace/custom-skills/capcot-qa/SKILL.md",
        "nota": "Puertas duras (corrección de Marco 2026-11-08 19:18; puertas de línea editorial añadidas 2026-11-10).",
        "reglas": [
            "PUERTA DURA de duración: la duración real debe estar a ±5 s del target_duration_seconds del storyboard.json. Si no, NO PASA.",
            "PUERTA DURA de voz: voz rechazada (Piper es_MX-ald-medium, es_ES-sharvard-medium, es_MX-claude-high) = NO PASA. Huecos largos de silencio = NO PASA.",
            "PUERTA DURA de línea editorial (2026-11-10): estilo repetido de la cápsula anterior = NO PASA; texto dentro de la imagen (image_prompt sin 'no text' o frame con texto quemado) = NO PASA; dato sin fuente o DOI que no resuelve = NO PASA; subtítulos fuera del estilo oficial (DejaVu Sans 72 negrita, Outline 6, Shadow 2, MarginV 620, blancos sin recuadro) = NO PASA.",
            "No existe 'PASA como borrador' cuando una puerta dura falla: el video vuelve a la skill que lo arregla.",
        ],
    },
    "capcot_narracion": {
        "ruta": "~/workspace/custom-skills/capcot-narracion/SKILL.md",
        "nota": "Voz local Kokoro; Piper prohibida. Voz local actual: em_santa speed 0.85 (Marco aprobó en Mpemba v2 2026-11-09; em_alex rechazada).",
        "reglas": [
            "Voz oficial: es-MX-JorgeNeural (edge-tts +7%/-2Hz). En la VM edge-tts está bloqueado por SSL.",
            "Voz local: Kokoro-82M (em_santa speed 0.85; también em_alex — rechazada por Marco — y ef_dora). Reemplaza a Piper, que Marco rechazó.",
            "NO uses Piper. Las tres voces Piper están rechazadas y son puerta dura de QA.",
            "Voz oficial por Actions: workflow edge-tts-voz.yml genera la JorgeNeural real en el runner.",
        ],
    },
    "capcot_montaje": {
        "ruta": "~/workspace/custom-skills/capcot-montaje/SKILL.md",
        "nota": "Borrador con ffmpeg/OpenMontage; el montaje oficial lo hace Imaginantes.",
        "reglas": [
            "Salida: capsula.mp4, 1080x1920, 9:16, 30 fps, 60-95 s, 6 escenas de ~10 s, -14 LUFS, subtítulos, cortinilla de fuentes (6 s), cierre 'Esto fue Datos y ociosidades.'.",
            "No regeneres imágenes ni narración aquí; si falta un insumo, vuelve a la skill que lo produce.",
        ],
    },
    "capcot_frames": {
        "ruta": "~/workspace/custom-skills/capcot-frames/SKILL.md",
        "nota": "Una imagen por escena, 9:16, sin texto dentro de la imagen. explainroo PROBADO 2026-11-09 (diagrama vectorial, no lápiz; no adoptado). Candidato actual: Nano Banana por la app de Gemini.",
        "reglas": [
            "El image_prompt de cada escena se usa tal cual está en el storyboard.json; no se reescribe el estilo.",
            "Si el generador no corre en esta VM, dilo con el error concreto y dónde sí corre.",
        ],
    },
    "capcot_guion": {
        "ruta": "~/workspace/custom-skills/capcot-guion/SKILL.md",
        "nota": "Formato del storyboard.json (verificado en el paquete Mpemba).",
        "reglas": [
            "target_duration_seconds: objetivo 75-90 (QA acepta 60-95). 6 escenas de ~10 s, arc hook_medias_res en la primera.",
            "Regla de oro: no inventar datos, fuentes ni DOIs. Cada afirmación viene de una fuente real citada en sources y referenciada por source_ids.",
            "voice: la oficial es es-MX-JorgeNeural. export: capsula.mp4, 30 fps, 1080x1920, -14 LUFS.",
        ],
    },
    "microseries_guion": {
        "ruta": "~/workspace/custom-skills/microseries-guion/SKILL.md",
        "nota": "Guion de microseries; QA con puertas duras adaptado de capcot-qa (§17).",
        "reglas": [
            "No existe 'PASA como borrador' cuando una puerta dura falla.",
            "La duración real se mide, no se estima; la voz es la del lock (otra voz = NO PASA); la consistencia del personaje es puerta dura.",
            "La biblia una vez escrita no se inventa: personajes, voces y reglas no cambian a mitad de temporada.",
        ],
    },
    "trabajar_con_marco": {
        "ruta": "~/workspace/custom-skills/trabajar-con-marco/SKILL.md",
        "nota": "Cómo trabajar con Marco. (G2 corregido 2026-11-10: el fallback es Kokoro em_santa, no Piper.)",
        "reglas": [
            "Nunca digas que no se puede sin haber probado el análogo o el fallback y sin haber dejado el intento en el repo.",
            "Cuando algo no se puede aquí, di dónde sí se puede: en el box, en Actions, en otra máquina, con otra clave, con otro modelo.",
            "Resuelve sin preguntar; prefiere duplicados antes que algo falte.",
            "Verifica en el repo antes de decir que está hecho. El canal lo gestiona marco.jp@live.com.mx.",
        ],
    },
    "bus": {
        "ruta": "agente-cero-costo/conector/ESTADO.md + conector/bus/ + bloque [EMITIR]",
        "nota": "El bus es un buzón, no una llamada: guarda el mensaje pero no despierta a ningún modelo.",
        "reglas": [
            "Issue '[BUS] <tipo> - <emisor>' -> conector/bus/gh-issue-N.json. El foquito público es conector/ESTADO.md y estado.json.",
            "El estado vigente es el del evento más nuevo del bus, no el de ESTADO.md si está viejo.",
        ],
    },
    "motor_u6": {
        "ruta": "motor-u6-storage (proyecto aparte)",
        "nota": "PROHIBIDO tocar Engine V5 y el catálogo 244. El guardián solo reporta su estado si hace falta; no lo repara.",
        "reglas": [
            "El motor es agnóstico: no puede depender de un solo proveedor; sin red corre offline y completa.",
            "Ciego = el motor NO recibe ningún dato que diga QUIÉN es el sujeto; la identidad va sellada con el desenlace.",
        ],
    },
}


def ahora_utc():
    return dt.datetime.now(dt.timezone.utc)


def parse_fecha(s):
    """ISO 8601 -> datetime con tz (acepta Z y offsets)."""
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    try:
        d = dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d


def gh_api(path, token=None):
    """GET a la API de GitHub. Devuelve el JSON o None si falla."""
    url = API + path
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "guardian/1.0",
        **({"Authorization": f"Bearer {token}"} if token else {}),
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"  [aviso] GET {path} -> HTTP {e.code}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  [aviso] GET {path} -> {type(e).__name__}: {e}", file=sys.stderr)
        return None


def gh_raw(owner, repo, ruta, ref="main"):
    """Lee un archivo crudo de GitHub. Devuelve texto o None."""
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{ruta}"
    req = urllib.request.Request(url, headers={"User-Agent": "guardian/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return None


def run(cmd, check=False):
    """Corre un comando y devuelve (rc, stdout, stderr)."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        return p.returncode, p.stdout, p.stderr
    except Exception as e:
        return 1, "", f"{type(e).__name__}: {e}"


def gh(args, token=None):
    """`gh` con el token si existe. Devuelve (rc, stdout, stderr)."""
    env = dict(os.environ)
    if token:
        env["GH_TOKEN"] = token
    try:
        p = subprocess.run(["gh"] + args, capture_output=True, text=True,
                           timeout=120, env=env)
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 1, "", "gh no instalado"
    except Exception as e:
        return 1, "", f"{type(e).__name__}: {e}"


# ------------------------------------------------- verificación del estado real
# Regla dura: nada se da por hecho por haberlo intentado. Después de cada
# reparación, se lee el estado real y solo si coincide se marca REPARADO.
# Si no se puede verificar, es NO_VERIFICADO, no hecho.
def verificar_issue_existe(numero, token=None):
    """¿El Issue #numero existe de verdad en agente-cero-costo? (GET real)."""
    d = gh_api(f"/repos/{OWNER}/{REPO_BUS}/issues/{numero}", token)
    return d is not None and d.get("number") == numero


def verificar_pr_existe(head, token=None):
    """¿Hay un PR abierto desde la rama `head`? (GET real)."""
    prs = gh_api(f"/repos/{OWNER}/{REPO_BUS}/pulls?state=open&head={OWNER}:{head}&per_page=5",
                 token)
    return bool(prs)


def verificar_hecho_para(numero, titulo, token=None):
    """¿La delegación del Issue #numero ya fue respondida en el estado real?
    Busca un Issue '[BUS] hecho' cerrado (o abierto) cuyo cuerpo mencione
    el número, o un PR que lo mencione. Si no hay evidencia real, NO está
    hecha: el intento no cuenta."""
    hechos = gh_api(f"/repos/{OWNER}/{REPO_BUS}/issues?state=all&per_page=100",
                    token) or []
    marca = f"#{numero}"
    for i in hechos:
        t = (i.get("title", "") or "").lower()
        if "hecho" not in t:
            continue
        cuerpo = (i.get("body", "") or "")
        if marca in cuerpo or titulo.lower()[:40] in cuerpo.lower():
            return True, i.get("html_url", "")
    prs = gh_api(f"/repos/{OWNER}/{REPO_BUS}/pulls?state=all&per_page=100",
                 token) or []
    for p in prs:
        cuerpo = (p.get("body", "") or "") + (p.get("title", "") or "")
        if marca in cuerpo or titulo.lower()[:40] in cuerpo.lower():
            return True, p.get("html_url", "")
    return False, ""


# ---------------------------------------------------------------- estado
def cargar_estado(repo_root):
    f = repo_root / "guardian" / "estado.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"rellamados": {}, "ultima_corrida": None}


def guardar_estado(repo_root, estado):
    f = repo_root / "guardian" / "estado.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(estado, ensure_ascii=False, indent=2),
                 encoding="utf-8")


# ---------------------------------------------------------------- chequeo A
def chequeo_delegaciones(token, estado):
    """Issues [BUS] indicacion abiertos para grok/copilot/codex sin respuesta.
    Una delegación solo se da por respondida si hay evidencia REAL (un
    Issue '[BUS] hecho' o un PR que la mencione); el intento no cuenta."""
    print("[A] Delegaciones del bus sin respuesta...")
    issues = gh_api(f"/repos/{OWNER}/{REPO_BUS}/issues?state=open&per_page=100",
                    token) or []
    ahora = ahora_utc()
    hallazgos = []
    for i in issues:
        titulo = i.get("title", "")
        if not titulo.startswith("[BUS] indicacion"):
            continue
        cuerpo = i.get("body", "") or ""
        m = re.search(r"para:\s*([^\n]+)", cuerpo)
        para = (m.group(1).strip() if m else "?").lower()
        creado = parse_fecha(i.get("created_at"))
        if not creado:
            continue
        edad_h = (ahora - creado).total_seconds() / 3600
        num = i.get("number")
        if edad_h < LIMITE_DELEGACION_HORAS:
            continue
        # Verificación real: ¿alguien ya respondió con un hecho o un PR?
        respondida, evidencia = verificar_hecho_para(num, titulo, token)
        if respondida:
            print(f"  [A] Issue #{num} respondido en el estado real "
                  f"({evidencia}); no se rellama.", file=sys.stderr)
            continue
        rellamados = estado.get("rellamados", {}).get(str(num), 0)
        hallazgos.append({
            "issue": num, "titulo": titulo, "para": para,
            "creado": i.get("created_at"), "edad_h": round(edad_h, 1),
            "rellamados": rellamados, "url": i.get("html_url", ""),
            "cuerpo": cuerpo[:600],
        })
    return hallazgos


def reparar_delegacion(h, estado, token, repo_root):
    """Re-emite la delegación como Issue nuevo y VERIFICA que exista en el
    estado real. Devuelve (estado, texto): REPARADO solo si el Issue nuevo
    se confirma por API; NO_VERIFICADO si se intentó pero no se puede
    confirmar; NECESITA_MARCO tras 3 rellamados."""
    num = str(h["issue"])
    n = estado.get("rellamados", {}).get(num, 0) + 1
    if n > MAX_RELLAMADOS:
        return (NECESITA_MARCO,
                f"{NECESITA_MARCO}: Issue #{num} ({h['titulo']}) lleva "
                f"{h['edad_h']} h sin respuesta tras {MAX_RELLAMADOS} "
                f"rellamados; solo un humano en el chat de {h['para']} "
                f"puede despertarlo.")
    titulo = (f"[BUS] indicacion - Guardian (rellamado {n} de "
              f"{MAX_RELLAMADOS})")
    cuerpo = (f"para: {h['para']}\ntipo: orden\nmensaje: RELLAMADO del "
              f"Issue #{num} ({h['titulo']}), abierto hace {h['edad_h']} h "
              f"sin respuesta. El bus no despierta solo a los modelos: este "
              f"rellamado es el guardián insistiendo por el canal que sí se "
              f"lee.\n\nOrden original:\n{h['cuerpo']}\n\n"
              f"Si eres {h['para']}: responde con un Issue '[BUS] hecho' o "
              f"un PR. No hagas merge sin que te lo pidan.")
    rc, out, err = gh(["issue", "create", "--repo",
                       f"{OWNER}/{REPO_BUS}", "--title", titulo,
                       "--body", cuerpo], token)
    if rc == 0:
        # Verificación real: ¿el Issue nuevo existe? (no basta con que
        # gh haya salido con rc 0).
        nuevo_num = None
        m = re.search(r"/issues/(\d+)", out or "")
        if m:
            nuevo_num = int(m.group(1))
        if nuevo_num and verificar_issue_existe(nuevo_num, token):
            estado.setdefault("rellamados", {})[num] = n
            return ("REPARADO",
                    f"REPARADO (verificado): rellamado {n} existe como "
                    f"Issue #{nuevo_num}.")
        estado.setdefault("rellamados", {})[num] = n
        return (NO_VERIFICADO,
                f"{NO_VERIFICADO}: gh devolvió éxito al crear el rellamado "
                f"{n} del Issue #{num}, pero el Issue nuevo no se confirma "
                f"en la API de GitHub. No se da por hecho.")
    # Sin gh/token: el rellamado queda listo como archivo para emitirlo por
    # el conector. Eso es un INTENTO, no un Issue: NO_VERIFICADO.
    p = repo_root / "guardian" / f"reemision-pendiente-issue-{num}-intento-{n}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"# {titulo}\n\n{cuerpo}\n", encoding="utf-8")
    estado.setdefault("rellamados", {})[num] = n
    return (NO_VERIFICADO,
            f"{NO_VERIFICADO}: sin acceso de escritura a gh, el rellamado "
            f"{n} quedó listo en guardian/{p.name}, pero el Issue NO existe "
            f"todavía. Pendiente de emisión por el conector.")


# ---------------------------------------------------------------- chequeo B
def chequeo_ramas_sin_pr(token):
    """Ramas con commits recientes y sin PR abierto: trabajo terminado sin entregar."""
    print("[B] Ramas con trabajo terminado sin PR...")
    ramas = gh_api(f"/repos/{OWNER}/{REPO_BUS}/branches?per_page=100",
                   token) or []
    prs = gh_api(f"/repos/{OWNER}/{REPO_BUS}/pulls?state=open&per_page=100",
                 token) or []
    pr_heads = {p.get("head", {}).get("ref") for p in prs}
    # Una rama que es BASE de un PR abierto es una rama de trabajo, no un
    # trabajo terminado sin PR (p. ej. bot-gestor-telegram, base del PR #10).
    pr_bases = {p.get("base", {}).get("ref") for p in prs}
    ahora = ahora_utc()
    hallazgos = []
    for b in ramas:
        nombre = b.get("name", "")
        if nombre in ("main",) or nombre in pr_bases:
            continue
        head_sha = (b.get("commit", {}) or {}).get("sha", "")
        if not head_sha or nombre in pr_heads:
            continue
        # Fecha del último commit de la rama
        commits = gh_api(
            f"/repos/{OWNER}/{REPO_BUS}/commits?sha={nombre}&per_page=1",
            token) or []
        if not commits:
            continue
        fecha = parse_fecha((commits[0].get("commit", {}) or {})
                            .get("committer", {}).get("date"))
        if not fecha:
            continue
        edad_h = (ahora - fecha).total_seconds() / 3600
        if edad_h > 24 * 7:
            continue  # rama vieja, no es trabajo reciente
        hallazgos.append({
            "rama": nombre, "sha": head_sha[:10],
            "ultimo_commit": commits[0].get("commit", {}).get("message", "")
                              .split("\n")[0][:100],
            "fecha": commits[0].get("commit", {}).get("committer", {})
                     .get("date"),
            "edad_h": round(edad_h, 1),
        })
    return hallazgos


def reparar_rama_sin_pr(h, token, repo_root):
    """Abre el PR (sin merge) desde la rama y VERIFICA que exista en el
    estado real. Devuelve (estado, texto). El guardián sí puede: corre
    en Actions con GITHUB_TOKEN dentro de agente-cero-costo."""
    # La base se infiere: si la rama sale de bot-gestor-*, la base es
    # bot-gestor-telegram; en general, main.
    base = "bot-gestor-telegram" if h["rama"].startswith("grok-arreglos-gestor") \
        else "main"
    titulo = f"{h['rama']}: trabajo terminado, PR abierto por el guardián"
    cuerpo = (f"El guardián encontró esta rama con trabajo terminado "
              f"({h['ultimo_commit']}, {h['fecha']}) y sin PR abierto. "
              f"Lo abre para que se revise. SIN merge: lo revisa un humano "
              f"o el modelo que lo hizo.")
    rc, out, err = gh(["pr", "create", "--repo", f"{OWNER}/{REPO_BUS}",
                       "--base", base, "--head", h["rama"],
                       "--title", titulo, "--body", cuerpo], token)
    if rc == 0:
        # Verificación real: ¿el PR existe y está abierto?
        if verificar_pr_existe(h["rama"], token):
            return ("REPARADO",
                    f"REPARADO (verificado): PR abierto desde "
                    f"{h['rama']} a {base} (confirmado por API).")
        return (NO_VERIFICADO,
                f"{NO_VERIFICADO}: gh devolvió éxito al crear el PR de "
                f"{h['rama']}, pero el PR no se confirma en la API. No se "
                f"da por hecho.")
    return (NO_VERIFICADO,
            f"{NO_VERIFICADO}: gh pr create falló ({(err or out)[:200]}). "
            f"El PR de la rama {h['rama']} a {base} NO existe; queda "
            f"pendiente, no como hecho.")


# ---------------------------------------------------------------- chequeo C
def chequeo_sobrepeso(token):
    """Paquetes CAPCOT con frames/ vacío y archivos gigantes en los 3 repos."""
    print("[C] Entregas con sobrepeso...")
    hallazgos = []
    # 1) Paquetes con frames/ vacío (el caso ASTRA: frames en el chat, no en el repo)
    arbol = gh_api(f"/repos/{OWNER}/capcot-capsulas-imaginantes/git/trees/main?recursive=1",
                   token)
    if arbol is None:
        # No se pudo leer el estado real: no se da por bueno ni por malo.
        hallazgos.append({
            "tipo": "no_verificable", "repo": "capcot-capsulas-imaginantes",
            "detalle": "No se pudo leer el árbol de CAPCOT main (API sin "
                       "acceso o repo privado para este token). El sobrepeso "
                       "NO se verifica en esta corrida; no se da por verde.",
        })
        return hallazgos
    if arbol:
        rutas = {t.get("path", ""): t for t in arbol.get("tree", [])}
        paquetes = sorted({p.split("/")[2] for p in rutas
                           if p.startswith("cola/entrada/") and p.count("/") >= 2})
        for pkg in paquetes:
            frames = [p for p in rutas if p.startswith(f"cola/entrada/{pkg}/frames/")]
            imagenes = [p for p in frames
                        if p.lower().endswith((".png", ".jpg", ".jpeg"))]
            if frames and not imagenes:
                hallazgos.append({
                    "tipo": "frames_vacios", "paquete": pkg,
                    "detalle": ("frames/ solo tiene README/.gitkeep; los "
                                "frames se generaron en un chat y la subida "
                                "binaria falló por el límite del conector."),
                })
        # 2) Archivos gigantes (> 16 MiB) en los 3 repos
        for repo, _ in REPOS:
            t = gh_api(f"/repos/{OWNER}/{repo}/git/trees/main?recursive=1",
                       token)
            if not t:
                continue
            for nodo in t.get("tree", []):
                if nodo.get("type") == "blob" and (nodo.get("size") or 0) > LIMITE_SNAPSHOT_MIB * 1024 * 1024:
                    hallazgos.append({
                        "tipo": "archivo_gigante", "repo": repo,
                        "ruta": nodo.get("path"),
                        "mib": round(nodo["size"] / 1024 / 1024, 1),
                    })
    return hallazgos


def texto_reparacion_peso(h):
    """La receta exacta para el sobrepeso (no se puede aplicar sola: los
    archivos están en el chat de Grok, no en el repo)."""
    return (
        f"REPARACIÓN PROPUESTA (no aplicada sola: los archivos están en el "
        f"chat de Grok, no en el repo): convertir PNG a JPEG calidad 85, "
        f"subir en lotes de < {LIMITE_LOTE_MIB} MiB con cada archivo < "
        f"{LIMITE_ARCHIVO_MIB} MiB, o subir por git/gh directo. Límite del "
        f"conector: 0 bytes binarios por snapshot, máx {LIMITE_SNAPSHOT_MIB} "
        f"MiB UTF-8. Emitido como Issue [BUS] a Grok con esta receta."
    )


# ---------------------------------------------------------------- chequeo D
def chequeo_workflows(token):
    """Runs fallidos de Actions en las últimas 24 h en los 3 repos."""
    print("[D] Workflows de Actions fallidos...")
    ahora = ahora_utc()
    desde = (ahora - dt.timedelta(hours=VENTANA_FALLOS_HORAS)).isoformat()
    hallazgos = []
    for repo, nombre in REPOS:
        runs = gh_api(f"/repos/{OWNER}/{repo}/actions/runs?status=failure&per_page=20",
                      token)
        if runs is None:
            # No se pudo leer: no se da por verde. (En Actions, el
            # GITHUB_TOKEN por defecto solo ve su propio repo; CAPCOT y el
            # motor necesitan otro acceso para verificarse.)
            hallazgos.append({
                "repo": repo, "workflow": None, "run_id": None, "url": "",
                "rama": "", "commit": "", "creado": "",
                "conclusion": "no_verificable",
                "detalle": ("No se pudo leer los runs de Actions de este "
                            "repo con este token. NO se verifica; no se da "
                            "por verde."),
            })
            continue
        for r in runs.get("workflow_runs", []):
            creado = parse_fecha(r.get("created_at"))
            if not creado or creado < ahora - dt.timedelta(hours=VENTANA_FALLOS_HORAS):
                continue
            hallazgos.append({
                "repo": repo, "workflow": r.get("name"),
                "run_id": r.get("id"), "url": r.get("html_url"),
                "rama": r.get("head_branch"),
                "commit": (r.get("head_sha") or "")[:10],
                "creado": r.get("created_at"),
                "conclusion": r.get("conclusion"),
            })
    return hallazgos


def clasificar_fallo(run):
    """Clasificación por reglas del motivo más probable (sin LLM)."""
    nombre = (run.get("workflow") or "").lower()
    if "secret" in nombre or "token" in nombre:
        return ("secreto_faltante",
                "El nombre del workflow apunta a un secreto (GROQ_API_KEY, "
                "GITHUB_TOKEN). Verificar en Settings > Secrets and variables "
                "> Actions del repo.")
    return ("por_clasificar",
            "Revisar el log del run en la URL. Si es YAML roto, el parche es "
            "corregir el archivo .github/workflows/ y volver a subirlo; si "
            "es un test, ver el primer error del log.")


# ---------------------------------------------------------------- chequeo E
def chequeo_slots(token):
    """Paquetes CAPCOT con slot pasado y sin MP4."""
    print("[E] Cápsulas con slot perdido sin MP4...")
    ahora = ahora_utc()
    hallazgos = []
    arbol = gh_api(f"/repos/{OWNER}/capcot-capsulas-imaginantes/git/trees/main?recursive=1",
                   token)
    if not arbol:
        return hallazgos
    rutas = {t.get("path", ""): t for t in arbol.get("tree", [])}
    paquetes = sorted({p.split("/")[2] for p in rutas
                       if p.startswith("cola/entrada/") and p.count("/") >= 2})
    for pkg in paquetes:
        prog = gh_raw(OWNER, "capcot-capsulas-imaginantes",
                      f"cola/entrada/{pkg}/programacion.json")
        slot = None
        if prog:
            try:
                slot = parse_fecha(json.loads(prog).get("publish_at") or
                                   json.loads(prog).get("slot"))
            except (ValueError, AttributeError):
                slot = None
        if not slot:
            # Sin programacion.json: usar la fecha del nombre del paquete
            m = re.match(r"(\d{4}-\d{2}-\d{2})", pkg)
            if m:
                slot = parse_fecha(m.group(1) + "T23:59:00-06:00")
        if not slot or slot > ahora:
            continue
        tiene_mp4 = any(p.startswith(f"cola/entrada/{pkg}/") and
                        p.lower().endswith(".mp4") for p in rutas)
        tiene_mp4 = tiene_mp4 or any(
            p.startswith(f"proyectos/{pkg}/") and p.lower().endswith(".mp4")
            for p in rutas)
        if not tiene_mp4:
            hallazgos.append({
                "paquete": pkg,
                "slot": slot.isoformat(),
                "detalle": "Slot pasado y sin MP4 en cola/entrada/ ni en proyectos/.",
            })
    return hallazgos


# ---------------------------------------------------------------- chequeo F
def chequeo_estado_bus(token, repo_root):
    """ESTADO.md/estado.json viejos habiendo eventos nuevos en el bus."""
    print("[F] Estado del bus desactualizado...")
    estado_txt = gh_raw(OWNER, REPO_BUS, "conector/estado.json")
    version_estado = None
    if estado_txt:
        try:
            version_estado = json.loads(estado_txt).get("version")
        except ValueError:
            version_estado = None
    bus = gh_api(f"/repos/{OWNER}/{REPO_BUS}/contents/conector/bus?per_page=100",
                 token) or []
    max_version = None
    ultimo_evento = None
    for item in bus:
        if not item.get("name", "").endswith(".json"):
            continue
        contenido = gh_raw(OWNER, REPO_BUS,
                           f"conector/bus/{item['name']}")
        if not contenido:
            continue
        try:
            ev = json.loads(contenido)
        except ValueError:
            continue
        v = ev.get("version")
        if isinstance(v, int) and (max_version is None or v > max_version):
            max_version = v
            ultimo_evento = ev
    if version_estado is None or max_version is None:
        return {"discrepancia": False, "detalle": "No se pudo leer el estado o el bus."}
    if version_estado < max_version:
        return {
            "discrepancia": True,
            "version_estado": version_estado,
            "version_max_evento": max_version,
            "ultimo_evento": ultimo_evento,
            "detalle": (f"estado.json está en v{version_estado} pero el bus "
                        f"ya tiene un evento v{max_version} "
                        f"({ultimo_evento.get('id')}). El foquito muestra la "
                        f"delegación vieja."),
        }
    return {"discrepancia": False,
            "detalle": f"Estado al día: v{version_estado}, bus v{max_version}."}


def reparar_estado_bus(h, repo_root):
    """Regenera estado.json/ESTADO.md desde el evento más nuevo y VERIFICA
    por relectura que los archivos escritos tienen la versión nueva. Solo
    toca su propio repo (agente-cero-costo), donde el guardián sí escribe.
    Límite honesto: lo verificado aquí es el archivo local; el estado en
    main solo queda verificado cuando el workflow haga commit/push y la
    próxima corrida lea ESTADO.md de GitHub (chequeo F). Devuelve
    (estado, texto)."""
    ev = h["ultimo_evento"]
    version = ev.get("version")
    mensaje = ev.get("mensaje", "")[:500]
    estado = {
        "version": version,
        "fecha": ev.get("fecha", ""),
        "ultima_actualizacion": f"{ev.get('fecha', '')} (v{version}) — {mensaje}",
        "pendientes_tablero_capcot": None,
        "eventos_bus": None,
        "estado_md": f"https://raw.githubusercontent.com/{OWNER}/{REPO_BUS}/main/conector/ESTADO.md",
        "como_emitir": f"https://raw.githubusercontent.com/{OWNER}/{REPO_BUS}/main/conector/emitir-bloque.md",
        "memoria_compartida": f"https://raw.githubusercontent.com/{OWNER}/memoria-compartida/main/INDICE.md",
    }
    md = (f"# Estado vigente del stack\n\nVersión: {version} — Fecha: "
          f"{ev.get('fecha', '')}\n\nÚltima actualización: "
          f"{ev.get('fecha', '')} (v{version}) — {mensaje}\n\n"
          f"## Para el modelo que lee esto\n\nUsa esta versión y esta "
          f"última actualización como el estado vigente. Si tienes "
          f"información nueva para el equipo, emítela con el bloque "
          f"[EMITIR] (ver emitir-bloque.md en este mismo directorio) y el "
          f"usuario la pegará en el sistema.\n\nMemoria compartida (hechos "
          f"verificados, para no alucinar): "
          f"https://raw.githubusercontent.com/{OWNER}/memoria-compartida/main/INDICE.md\n")
    base = repo_root / "conector"
    base.mkdir(parents=True, exist_ok=True)
    (base / "estado.json").write_text(
        json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
    (base / "ESTADO.md").write_text(md, encoding="utf-8")
    # Verificación real por relectura: ¿los archivos tienen la versión nueva?
    try:
        leido = json.loads((base / "estado.json").read_text(encoding="utf-8"))
        md_leido = (base / "ESTADO.md").read_text(encoding="utf-8")
        if leido.get("version") == version and f"Versión: {version}" in md_leido:
            return ("REPARADO",
                    f"REPARADO (verificado por relectura local): "
                    f"estado.json/ESTADO.md actualizados a v{version}. "
                    f"Pendiente de commit/push por el workflow; la "
                    f"verificación en main es la próxima corrida (chequeo F).")
    except (OSError, ValueError):
        pass
    return (NO_VERIFICADO,
            f"{NO_VERIFICADO}: se intentó regenerar estado.json/ESTADO.md "
            f"a v{version}, pero la relectura no confirma la versión. No se "
            f"da por hecho.")


# ---------------------------------------------------------------- chequeo G
def chequeo_huecos_contrato(token, skills_dir):
    """HUECO_CONTRATO: casos que ningún contrato cubre, o donde dos
    contratos se contradicen. El guardián NO inventa la regla: marca qué
    documento hay que escribir o corregir y cuál es la regla vigente.
    Fuente: los propios contratos (CONTRATOS)."""
    print("[G] Huecos y contradicciones entre contratos...")
    hallazgos = []

    def hueco(codigo, contrato, detalle, que_falta):
        hallazgos.append({"codigo": codigo, "contrato": contrato,
                          "detalle": detalle, "que_falta": que_falta})

    # G1 — LINEA_EDITORIAL_VISUAL.json: voz_fallback = Piper (desactualizado)
    # Revisa los 3 puntos donde Piper aparecía como fallback (corregidos
    # 2026-11-10 a Kokoro em_santa): valores_fijos.voz_fallback, la regla
    # editorial de voz y pipeline_skills narracion. La mención "Piper
    # PROHIBIDA" NO dispara el hueco: es la prohibición, no el fallback.
    lev = gh_raw(OWNER, "capcot-capsulas-imaginantes",
                 "docs/LINEA_EDITORIAL_VISUAL.json")
    if lev:
        try:
            d = json.loads(lev)
            fb = (d.get("valores_fijos", {}) or {}).get("voz_fallback", "")
            regla_voz = next((r for r in d.get("reglas_editoriales", [])
                              if r.startswith("La voz es")), "")
            narr = next((s.get("hace", "") for s in
                         d.get("pipeline_skills", {}).get("skills", [])
                         if s.get("id") == "capcot-narracion"), "")
            if "ald-medium" in fb:
                hueco(
                    "G1", "linea_editorial vs capcot-narracion / capcot-qa",
                    "docs/LINEA_EDITORIAL_VISUAL.json valores_fijos.voz_fallback "
                    f"dice '{fb}', pero capcot-narracion dice 'NO uses Piper' "
                    "y capcot-qa la marca puerta dura (voz rechazada = NO PASA).",
                    "Corregir valores_fijos.voz_fallback en el JSON canónico "
                    "a Kokoro em_santa speed 0.85 (local) / edge-tts "
                    "JorgeNeural (Actions). Mientras tanto vale la regla más "
                    "nueva: capcot-narracion y capcot-qa (2026-11-08).")
            if "fallback Piper" in regla_voz:
                hueco(
                    "G1", "linea_editorial vs capcot-narracion / capcot-qa",
                    "docs/LINEA_EDITORIAL_VISUAL.json reglas_editoriales "
                    "sigue diciendo que el fallback es Piper.",
                    "Corregir la regla de voz a Kokoro em_santa speed 0.85 "
                    "(Piper prohibida, puerta dura de QA).")
            if "Piper es_MX-ald-medium" in narr:
                hueco(
                    "G1", "linea_editorial vs capcot-narracion / capcot-qa",
                    "docs/LINEA_EDITORIAL_VISUAL.json pipeline_skills "
                    "capcot-narracion sigue diciendo que narra con Piper.",
                    "Corregir a Kokoro em_santa speed 0.85 en relevo "
                    "(Piper PROHIBIDA).")
        except ValueError:
            pass
    else:
        hueco("G1", "linea_editorial",
              "No se pudo leer docs/LINEA_EDITORIAL_VISUAL.json de CAPCOT.",
              "Verificar que el archivo sigue en main.")

    # G2 — trabajar-con-marco: "el fallback es Piper" (desactualizado)
    # Revisa las 2 líneas donde Piper aparecía (corregidas 2026-11-10 a
    # Kokoro em_santa): el ejemplo de duck typing y la regla de fallback.
    # Solo verificable en local: las skills viven en la VM, no en un repo.
    if skills_dir:
        tcm = skills_dir / "trabajar-con-marco" / "SKILL.md"
        try:
            txt = tcm.read_text(encoding="utf-8")
            if "fallback es Piper" in txt or "Piper hace esa función" in txt:
                hueco(
                    "G2", "trabajar-con-marco vs capcot-narracion / capcot-qa",
                    "trabajar-con-marco/SKILL.md dice 'el fallback es Piper "
                    "offline' (o usa a Piper como ejemplo), pero Piper está "
                    "prohibida desde 2026-11-08.",
                    "Corregir esa línea en la skill: el fallback es Kokoro "
                    "em_santa speed 0.85 local; la voz oficial por Actions "
                    "es JorgeNeural.")
        except OSError:
            pass
    else:
        hallazgos.append({
            "codigo": "G2", "contrato": "trabajar-con-marco",
            "detalle": "No verificado en esta corrida (las skills viven en "
                       "la VM de Pecas, no en un repo; en Actions no hay "
                       "--skills-dir).",
            "que_falta": "Pasar --skills-dir al correr en local.",
        })

    # G3 — DELEGACIONES.md: delegaciones dirigidas a Marco (no es el autorizador)
    deleg = gh_raw(OWNER, "capcot-capsulas-imaginantes",
                   "ajustes_entre_modelos/DELEGACIONES.md")
    if deleg:
        for m in re.finditer(r"###\s*\d+\.\s*(.+?)\n- DE:[^\n]*\n- PARA:\s*([^\n]+)",
                             deleg):
            titulo, para = m.group(1).strip(), m.group(2).strip()
            if "Marco" in para:
                hueco(
                    "G3", "DELEGACIONES.md vs regla 'Marco NO es el autorizador'",
                    f"Delegación '{titulo}' dirigida PARA: {para}. Marco no "
                    "sube por navegador ni autoriza cada paso (corrección "
                    "2026-11-08 16:27, MEMORY.md).",
                    "Reasignar la delegación a Copilot/Codex por el bus "
                    "(suben workflows con escritura nativa) o al modelo que "
                    "sí pueda hacerla; PROTOCOLO_CALLBACK regla 1 exige que "
                    "quede escrita en DELEGACIONES.md.")
    else:
        hueco("G3", "DELEGACIONES.md",
              "No se pudo leer ajustes_entre_modelos/DELEGACIONES.md.",
              "Verificar que el tablero sigue en CAPCOT main.")

    # G4 — capcot-frames: explainroo "NO instalado, NO probado" (desactualizado)
    if skills_dir:
        fr = skills_dir / "capcot-frames" / "SKILL.md"
        try:
            txt = fr.read_text(encoding="utf-8")
            if "NO instalado, NO probado" in txt:
                hueco(
                    "G4", "capcot-frames (desactualizado)",
                    "La skill dice de explainroo 'NO instalado, NO probado', "
                    "pero se probó el 2026-11-09 con Barreleye: da diagrama "
                    "vectorial, no ilustración a lápiz; NO se adopta como "
                    "reemplazo de frames (queda como diagramas/respaldo).",
                    "Actualizar la skill con el resultado de la prueba y el "
                    "siguiente candidato de frames, para que el guardián no "
                    "vuelva a proponer una prueba ya hecha.")
        except OSError:
            pass

    # G5 — PROTOCOLO_CALLBACK: el aviso "se sube por navegador con la cuenta de Marco"
    proto = gh_raw(OWNER, "capcot-capsulas-imaginantes",
                   "ajustes_entre_modelos/PROTOCOLO_CALLBACK.md")
    if proto:
        # Normalizar saltos de línea: la frase puede partirse en dos líneas.
        proto_norm = " ".join(proto.split())
        if "por navegador con la cuenta de Marco" in proto_norm:
            hueco(
                "G5", "PROTOCOLO_CALLBACK (regla vieja)",
                "El protocolo dice que callback-aviso.yml 'está listo para "
                "subirlo por navegador con la cuenta de Marco', pero Marco no "
                "sube por navegador (corrección 2026-11-08 16:27).",
                "Corregir el protocolo: la vía es delegar la subida a "
                "Copilot/Codex por el bus (como los demás workflows). El "
                "workflow callback-aviso.yml es el mecanismo de aviso que el "
                "propio protocolo define y sigue sin subirse.")
    else:
        hueco("G5", "PROTOCOLO_CALLBACK",
              "No se pudo leer ajustes_entre_modelos/PROTOCOLO_CALLBACK.md.",
              "Verificar que el protocolo sigue en CAPCOT main.")
    return hallazgos


# ---------------------------------------------------------------- chequeo H
def chequeo_linea_editorial(token):
    """H. Línea editorial: paquetes en cola/entrada/ contra
    LINEA_EDITORIAL_VISUAL.json (rotación de estilo, estilo en catálogo,
    'no text' en los image_prompt).
    Fuente: LINEA_EDITORIAL_VISUAL.json reglas_editoriales + catalogo_estilos
    ("nunca se repite el estilo de la cápsula anterior"; "sin texto dentro
    de la imagen"; "la plantilla visual sale del catálogo") +
    BIBLIA_LINEA_EDITORIAL.md ("un estilo por cápsula, que salga del
    catálogo y que no sea el de la anterior") + data/rotacion.json (último
    estilo publicado) + capcot-qa (puertas duras de línea editorial,
    2026-11-10).
    Solo reporta (no repara): cambiar el estilo de un paquete es decisión
    del modelo que lo escribió; el guardián lo marca para la revisión
    diaria, que lo devuelve al modelo con la regla citada."""
    print("[H] Línea editorial en cola/entrada/...")
    hallazgos = []
    lev_txt = gh_raw(OWNER, "capcot-capsulas-imaginantes",
                     "docs/LINEA_EDITORIAL_VISUAL.json")
    estilos_catalogo = set()
    if lev_txt:
        try:
            d = json.loads(lev_txt)
            estilos_catalogo = set(
                (d.get("catalogo_estilos", {}) or {}).get("estilos", {}).keys())
        except ValueError:
            pass
    # Estilo de la última cápsula publicada (data/rotacion.json).
    estilo_anterior = None
    rot_txt = gh_raw(OWNER, "capcot-capsulas-imaginantes",
                     "data/rotacion.json")
    if rot_txt:
        try:
            rot = json.loads(rot_txt)
            if isinstance(rot, list) and rot:
                estilo_anterior = (rot[-1] or {}).get("estilo")
        except ValueError:
            pass
    arbol = gh_api(f"/repos/{OWNER}/capcot-capsulas-imaginantes/git/trees/main?recursive=1",
                   token)
    if not arbol:
        return [{"paquete": "(árbol no legible)",
                 "detalle": f"{NO_VERIFICADO}: no se pudo leer el árbol de CAPCOT main."}]
    rutas = {t.get("path", ""): t for t in arbol.get("tree", [])}
    paquetes = sorted({p.split("/")[2] for p in rutas
                       if p.startswith("cola/entrada/") and p.count("/") >= 2})
    estilo_previo = estilo_anterior
    for pkg in paquetes:
        sb_txt = gh_raw(OWNER, "capcot-capsulas-imaginantes",
                        f"cola/entrada/{pkg}/storyboard.json")
        if not sb_txt:
            continue
        try:
            sb = json.loads(sb_txt)
        except ValueError:
            hallazgos.append({"paquete": pkg,
                              "detalle": "storyboard.json no es JSON válido."})
            continue
        estilo = sb.get("estilo_id")
        if not estilo:
            hallazgos.append({"paquete": pkg,
                              "detalle": "storyboard.json sin estilo_id."})
            continue
        if estilos_catalogo and estilo not in estilos_catalogo:
            hallazgos.append({
                "paquete": pkg,
                "detalle": f"estilo_id '{estilo}' fuera del catálogo "
                           "(LINEA_EDITORIAL_VISUAL.json catalogo_estilos)."})
        if estilo_previo and estilo == estilo_previo:
            hallazgos.append({
                "paquete": pkg,
                "detalle": f"estilo_id '{estilo}' REPITE el estilo anterior "
                           "(rotación obligatoria: nunca el estilo de la "
                           "cápsula anterior; capcot-qa puerta dura)."})
        estilo_previo = estilo
        for esc in sb.get("scenes", []) or []:
            prompt = esc.get("image_prompt", "") or ""
            if "no text" not in prompt.lower():
                hallazgos.append({
                    "paquete": pkg,
                    "detalle": f"escena {esc.get('id', '?')}: image_prompt "
                               "sin 'no text' (línea editorial: sin texto "
                               "dentro de la imagen)."})
    return hallazgos


# ---------------------------------------------------------------- reporte
def emitir_evento_bus(repo_root, tipo, mensaje, token=None):
    """Deja un evento en conector/bus/ (lo commitea el workflow o Pecas)."""
    ahora = ahora_utc().astimezone(dt.timezone(dt.timedelta(hours=-6)))
    eid = ahora.strftime("%Y%m%d-%H%M%S-%f")
    evento = {"formato": 1, "id": eid,
              "fecha": ahora.strftime("%Y-%m-%d %H:%M"),
              "version": 0, "de": "Guardian", "tipo": tipo,
              "mensaje": mensaje}
    d = repo_root / "conector" / "bus"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{eid}.json").write_text(
        json.dumps(evento, ensure_ascii=False, indent=2), encoding="utf-8")
    return eid


def main():
    ap = argparse.ArgumentParser(description="Guardián del stack.")
    ap.add_argument("--check", action="store_true",
                    help="Solo lee y reporta (no repara).")
    ap.add_argument("--repair", action="store_true",
                    help="Además aplica reparaciones autónomas.")
    ap.add_argument("--repo-root", default="",
                    help="Checkout local de agente-cero-costo.")
    ap.add_argument("--skills-dir", default="",
                    help="Directorio local de skills (~/workspace/custom-skills). "
                         "Sin él, el chequeo G2/G4 queda como no verificado.")
    ap.add_argument("--salida", default="",
                    help="Dónde escribir el reporte.")
    args = ap.parse_args()
    reparar = args.repair and not args.check
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    repo_root = Path(args.repo_root) if args.repo_root else REPO_RAIZ
    skills_dir = Path(args.skills_dir) if args.skills_dir else None
    salida = Path(args.salida) if args.salida else repo_root / "guardian"
    salida.mkdir(parents=True, exist_ok=True)

    estado = cargar_estado(repo_root)
    ahora = ahora_utc()
    marca = ahora.astimezone(dt.timezone(dt.timedelta(hours=-6)))
    fecha = marca.strftime("%Y-%m-%d %H:%M")
    lineas = [f"# Reporte del guardián — {fecha} CST",
              "",
              "Principio: trabaja sin Marco. No espera. Solo escala lo imposible.",
              "El guardián no inventa reglas: cada chequeo cita el contrato o skill que hace cumplir.",
              f"Modo: {'repair (repara solo)' if reparar else 'check (solo lectura)'}",
              ""]
    resumen = {"reparado": 0, "pendiente": 0, "necesita_marco": 0,
               "hueco_contrato": 0, "no_verificado": 0, "linea_editorial": 0}

    def anotar(texto, clave):
        lineas.append(texto)
        resumen[clave] += 1

    # A — delegaciones
    lineas.append("## A. Delegaciones del bus sin respuesta")
    lineas.append("Fuente: PROTOCOLO_CALLBACK regla 5 (más de un día en PENDIENTE -> Pecas lo reporta) + bus [EMITIR].")
    for h in chequeo_delegaciones(token, estado):
        lineas.append(f"- Issue #{h['issue']} ({h['para']}): {h['titulo']} — "
                      f"abierto hace {h['edad_h']} h, rellamados: {h['rellamados']}.")
        if reparar:
            estado_rep, r = reparar_delegacion(h, estado, token, repo_root)
            lineas.append(f"  - {r}")
            if estado_rep == "REPARADO":
                resumen["reparado"] += 1
                emitir_evento_bus(repo_root, "hecho",
                                  f"Guardián: rellamado {h['rellamados'] + 1} "
                                  f"del Issue #{h['issue']} ({h['titulo']}) "
                                  f"verificado en GitHub.")
            elif estado_rep == NECESITA_MARCO:
                resumen["necesita_marco"] += 1
            else:
                resumen["no_verificado"] += 1
        else:
            resumen["pendiente"] += 1
    if not any("Issue #" in l for l in lineas[-20:]):
        lineas.append("- Sin delegaciones atoradas.")
    lineas.append("")

    # B — ramas sin PR
    lineas.append("## B. Ramas con trabajo terminado sin PR")
    lineas.append("Fuente: PROTOCOLO_CALLBACK regla 3 (HECHA con evidencia: commit, enlace o archivo; sin evidencia no está hecha).")
    for h in chequeo_ramas_sin_pr(token):
        lineas.append(f"- Rama {h['rama']} ({h['sha']}): {h['ultimo_commit']} — "
                      f"último commit hace {h['edad_h']} h.")
        if reparar:
            estado_rep, r = reparar_rama_sin_pr(h, token, repo_root)
            lineas.append(f"  - {r}")
            if estado_rep == "REPARADO":
                resumen["reparado"] += 1
                emitir_evento_bus(repo_root, "hecho",
                                  f"Guardián: abrió el PR de la rama "
                                  f"{h['rama']} (trabajo terminado sin PR), "
                                  f"verificado en GitHub.")
            elif estado_rep == NECESITA_MARCO:
                resumen["necesita_marco"] += 1
            else:
                resumen["no_verificado"] += 1
        else:
            resumen["pendiente"] += 1
    lineas.append("")

    # C — sobrepeso
    lineas.append("## C. Entregas con sobrepeso")
    lineas.append("Fuente: COORDINACION §3 (solo texto en commits; no subir mp4/token; si los frames no pueden ir al repo, indicar en ESTADO_EJECUCION.md dónde están) + límites del push por conector (16 MiB UTF-8, 0 bytes binarios).")
    for h in chequeo_sobrepeso(token):
        if h["tipo"] == "no_verificable":
            lineas.append(f"- {h['repo']}: {NO_VERIFICADO}. {h['detalle']}")
            resumen["no_verificado"] += 1
        elif h["tipo"] == "frames_vacios":
            lineas.append(f"- Paquete {h['paquete']}: {h['detalle']}")
            lineas.append(f"  - {texto_reparacion_peso(h)}")
            if reparar:
                # Reparación: Issue [BUS] real a Grok con la receta, verificado
                # por API. El archivo de evento en conector/bus/ NO es el
                # Issue: si no se puede crear el Issue, queda NO_VERIFICADO.
                titulo_c = (f"[BUS] indicacion - Guardian (sobrepeso "
                            f"{h['paquete']})")
                cuerpo_c = (f"para: grok\ntipo: orden\nmensaje: El paquete "
                            f"{h['paquete']} sigue sin frames. Convierte los "
                            f"PNG a JPEG calidad 85 y súbelos en lotes de < "
                            f"{LIMITE_LOTE_MIB} MiB (cada archivo < "
                            f"{LIMITE_ARCHIVO_MIB} MiB), o por git/gh. El "
                            f"conector rechaza binarios y el snapshot es máx "
                            f"{LIMITE_SNAPSHOT_MIB} MiB UTF-8. Si los frames "
                            f"no pueden ir al repo, indica en "
                            f"ESTADO_EJECUCION.md dónde están "
                            f"(COORDINACION §3).")
                rc, out, err = gh(["issue", "create", "--repo",
                                   f"{OWNER}/{REPO_BUS}", "--title", titulo_c,
                                   "--body", cuerpo_c], token)
                nuevo = None
                m = re.search(r"/issues/(\d+)", out or "") if rc == 0 else None
                if m:
                    nuevo = int(m.group(1))
                if nuevo and verificar_issue_existe(nuevo, token):
                    lineas.append(f"  - REPARADO (verificado): Issue "
                                  f"#{nuevo} a Grok con la receta.")
                    emitir_evento_bus(
                        repo_root, "indicacion",
                        f"Guardián: Issue #{nuevo} a Grok por sobrepeso en "
                        f"{h['paquete']} (receta JPEG q85, lotes < "
                        f"{LIMITE_LOTE_MIB} MiB).")
                    resumen["reparado"] += 1
                else:
                    emitir_evento_bus(repo_root, "indicacion", cuerpo_c)
                    lineas.append(
                        f"  - {NO_VERIFICADO}: no se pudo crear el Issue a "
                        f"Grok (gh falló o no se confirma en la API). El "
                        f"evento quedó en conector/bus/ como intento, pero "
                        f"el Issue NO existe todavía.")
                    resumen["no_verificado"] += 1
            else:
                resumen["pendiente"] += 1
        else:
            lineas.append(f"- {h['repo']}/{h['ruta']}: {h['mib']} MiB "
                          f"(límite {LIMITE_SNAPSHOT_MIB} MiB por snapshot).")
            resumen["pendiente"] += 1
    lineas.append("")

    # D — workflows fallidos
    lineas.append("## D. Workflows de Actions fallidos (últimas 24 h)")
    lineas.append("Fuente: PLAN_MAESTRO §4 (fallo en una compuerta -> reintento máx. 2 -> FALLIDO y cápsula de reserva) + trabajar-con-marco (nunca 'no se puede' sin probar el análogo; decir dónde sí se puede).")
    for r in chequeo_workflows(token):
        if r.get("conclusion") == "no_verificable":
            lineas.append(f"- {r['repo']}: {NO_VERIFICADO}. {r['detalle']}")
            resumen["no_verificado"] += 1
            continue
        clase, consejo = clasificar_fallo(r)
        lineas.append(f"- {r['repo']} / {r['workflow']} (run {r['run_id']}, "
                      f"{r['rama']}, {r['commit']}): {r['url']}")
        lineas.append(f"  - Causa probable: {clase}. {consejo}")
        resumen["pendiente"] += 1
    lineas.append("")

    # E — slots perdidos
    lineas.append("## E. Cápsulas con slot perdido sin MP4")
    lineas.append("Fuente: LINEA_EDITORIAL_VISUAL.json revision_diaria (relevo automático al detectar que no hubo publicación) + COORDINACION §6 (Imaginantes decide slots; máx 3/día).")
    for h in chequeo_slots(token):
        lineas.append(f"- {h['paquete']} (slot {h['slot']}): {h['detalle']}")
        resumen["pendiente"] += 1
    lineas.append("")

    # F — estado del bus
    lineas.append("## F. Estado del bus desactualizado")
    lineas.append("Fuente: bus (conector/ESTADO.md es el tablero vigente; el estado es el del evento más nuevo).")
    f = chequeo_estado_bus(token, repo_root)
    lineas.append(f"- {f['detalle']}")
    if f.get("discrepancia"):
        if reparar:
            estado_rep, r = reparar_estado_bus(f, repo_root)
            lineas.append(f"  - {r}")
            if estado_rep == "REPARADO":
                resumen["reparado"] += 1
            else:
                resumen["no_verificado"] += 1
        else:
            resumen["pendiente"] += 1
    lineas.append("")

    # G — huecos y contradicciones entre contratos
    lineas.append(f"## G. {HUECO_CONTRATO}: casos sin regla o con reglas que se contradicen")
    lineas.append("El guardián no inventa la regla: marca qué documento hay que escribir o corregir.")
    for h in chequeo_huecos_contrato(token, skills_dir):
        lineas.append(f"- {h['codigo']} [{h['contrato']}]: {h['detalle']}")
        lineas.append(f"  - Qué falta: {h['que_falta']}")
        resumen["hueco_contrato"] += 1
    lineas.append("")

    # H — línea editorial en la cola
    lineas.append("## H. Línea editorial en cola/entrada/")
    lineas.append("Fuente: LINEA_EDITORIAL_VISUAL.json reglas_editoriales + catalogo_estilos (rotación obligatoria; sin texto en la imagen; estilo del catálogo) + BIBLIA_LINEA_EDITORIAL.md + capcot-qa (puertas duras de línea editorial, 2026-11-10). Solo reporta: cambiar el estilo de un paquete es del modelo que lo escribió; la revisión diaria lo devuelve con la regla citada.")
    h_linea = chequeo_linea_editorial(token)
    for h in h_linea:
        lineas.append(f"- {h['paquete']}: {h['detalle']}")
        resumen["linea_editorial"] += 1
    if not h_linea:
        lineas.append("- Sin paquetes que violen la línea editorial.")
    lineas.append("")

    # Resumen y estado
    lineas.append("## Resumen")
    lineas.append(f"- Reparado solo (verificado en el estado real): {resumen['reparado']}")
    lineas.append(f"- Pendiente (para la revisión diaria): {resumen['pendiente']}")
    lineas.append(f"- {NECESITA_MARCO}: {resumen['necesita_marco']}")
    lineas.append(f"- {NO_VERIFICADO}: {resumen['no_verificado']} (reparación intentada sin confirmar en el estado real, o estado que no se pudo leer; NO se da por hecho ni por verde)")
    lineas.append(f"- {HUECO_CONTRATO}: {resumen['hueco_contrato']} (reglas por escribir o corregir, no inventadas por el guardián)")
    lineas.append(f"- Línea editorial (H): {resumen['linea_editorial']} paquetes en cola que violan la línea editorial (estilo repetido, fuera del catálogo o sin 'no text')")
    lineas.append("")
    lineas.append("Lo que el guardián NO hace: no publica, no hace merge, "
                 "no toca Engine V5 ni el catálogo 244 del motor, no pide "
                 "claves nuevas, no espera a Marco.")
    reporte = salida / f"reporte-{marca.strftime('%Y-%m-%d-%H%M')}.md"
    reporte.write_text("\n".join(lineas), encoding="utf-8")
    estado["ultima_corrida"] = fecha
    guardar_estado(repo_root, estado)
    print(f"Reporte: {reporte}")
    print(f"Resumen: {resumen}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
