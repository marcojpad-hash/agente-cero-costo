#!/usr/bin/env python3
"""Bot gestor de Telegram: un solo bot que habla por todos los motores.

Telegram (long polling) -> motores gratis en paralelo -> gestor final
(system prompt de PROMPT_GESTOR.md) -> una sola respuesta.

Solo stdlib. Las claves se leen SOLO de variables de entorno.
Un motor sin clave se salta; no tumba al bot.
"""
import json
import re
import os
import sys
import time
import uuid
import urllib.error
import urllib.request
import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = AQUI.parent
BUS = REPO / "conector" / "bus"
DIGEST = REPO / "memoria-digest" / "DIGEST.md"
GROQ_CHAT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_AUDIO = "https://api.groq.com/openai/v1/audio/transcriptions"
OPENROUTER_CHAT = "https://openrouter.ai/api/v1/chat/completions"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
TG_API = "https://api.telegram.org/bot{token}/{method}"
TG_FILE = "https://api.telegram.org/file/bot{token}/{path}"
ESTADO_URL = "https://raw.githubusercontent.com/marcojpad-hash/agente-cero-costo/main/conector/ESTADO.md"
TG_LIMITE = 4096
TIPOS_EMITIR = ["actualizacion", "indicacion", "aviso", "hecho"]

IDENTIDAD = (
    "Eres el Gestor Mj. Resuelves en primera persona. "
    "No hables de tokenización ni de cómo funcionas internamente. "
    "No des código salvo que Mj lo pida explícitamente. "
    "Nunca respondas solo 'no se puede'; siempre da el camino que sí funciona."
)


def env(nombre, defecto=None):
    v = os.environ.get(nombre, "").strip()
    return v or defecto


def cargar_prompt(ruta=None):
    ruta = Path(ruta or env("GESTOR_PROMPT_FILE", str(AQUI / "PROMPT_GESTOR.md")))
    texto = ruta.read_text(encoding="utf-8").strip()
    if not texto:
        raise SystemExit(f"el prompt del gestor está vacío: {ruta}")
    return texto


def chats_permitidos():
    """Conjunto de chat ids permitidos. Vacío = nadie (falla cerrado)."""
    crudo = env("TELEGRAM_ALLOWED_CHAT_IDS", "")
    return {p.strip() for p in crudo.replace(";", ",").split(",") if p.strip()}


def permitido(chat_id, permitidos=None):
    permitidos = chats_permitidos() if permitidos is None else permitidos
    return bool(permitidos) and str(chat_id) in permitidos


def http_json(url, payload=None, headers=None, timeout=60):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    h = {"Content-Type": "application/json", "User-Agent": "bot-gestor/1.0"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def http_bytes(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "bot-gestor/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# ---------- motores ----------

def _openai_chat(url, key, model, messages, timeout):
    d = http_json(url, {"model": model, "messages": messages},
                  {"Authorization": f"Bearer {key}"}, timeout)
    return d["choices"][0]["message"]["content"].strip()


def _gemini(key, model, messages, timeout):
    system = "\n".join(m["content"] for m in messages if m["role"] == "system")
    contents = [{"role": "model" if m["role"] == "assistant" else "user",
                 "parts": [{"text": m["content"]}]}
                for m in messages if m["role"] != "system"]
    payload = {"contents": contents}
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    d = http_json(GEMINI_URL.format(model=model), payload,
                  {"x-goog-api-key": key}, timeout)
    partes = d["candidates"][0]["content"]["parts"]
    return "".join(p.get("text", "") for p in partes).strip()


def motores_config():
    """Lista de motores con su clave presente. Los que no tienen clave no aparecen."""
    candidatos = [
        ("groq-gpt-oss", "GROQ_API_KEY", "groq", env("MOTOR_GROQ_MODEL", "openai/gpt-oss-120b")),
        ("groq-2", "GROQ_API_KEY", "groq", env("MOTOR_GROQ2_MODEL", "openai/gpt-oss-20b")),
        ("gemini", "GEMINI_API_KEY", "gemini", env("MOTOR_GEMINI_MODEL", "gemini-3.8-flash")),
        ("openrouter", "OPENROUTER_API_KEY", "openrouter",
         env("MOTOR_OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")),
    ]
    apagados = {x.strip() for x in env("MOTORES_APAGADOS", "").split(",") if x.strip()}
    out = []
    for nombre, var, tipo, model in candidatos:
        key = env(var)
        if key and nombre not in apagados:
            out.append({"nombre": nombre, "tipo": tipo, "model": model, "key": key})
    return out


def llamar_motor(m, messages, timeout=None):
    timeout = timeout or int(env("MOTOR_TIMEOUT", "60"))
    if m["tipo"] == "groq":
        return _openai_chat(GROQ_CHAT, m["key"], m["model"], messages, timeout)
    if m["tipo"] == "openrouter":
        return _openai_chat(OPENROUTER_CHAT, m["key"], m["model"], messages, timeout)
    if m["tipo"] == "gemini":
        return _gemini(m["key"], m["model"], messages, timeout)
    raise ValueError(f"motor desconocido: {m['tipo']}")


def consultar_motores(pregunta, historial, motores=None):
    """Llama a todos los motores en paralelo. Devuelve {nombre: texto o 'ERROR: ...'}."""
    motores = motores_config() if motores is None else motores
    messages = [{"role": "system", "content": IDENTIDAD}]
    messages += historial + [{"role": "user", "content": pregunta}]
    resultados = {}
    if not motores:
        return resultados
    with ThreadPoolExecutor(max_workers=len(motores)) as ex:
        futuros = {m["nombre"]: ex.submit(llamar_motor, m, messages) for m in motores}
        for nombre, f in futuros.items():
            try:
                resultados[nombre] = f.result()
            except Exception as e:  # un motor caído no tumba al resto
                resultados[nombre] = f"ERROR: {type(e).__name__}: {str(e)[:200]}"
    return resultados


def entrada_gestor(pregunta, respuestas):
    bloques = [f"PREGUNTA DE MJ:\n{pregunta}\n", "RESPUESTAS DE LOS MOTORES:"]
    if not respuestas:
        bloques.append("(ningún motor respondió)")
    for nombre, texto in respuestas.items():
        texto = (texto or "")[:3000]
        bloques.append(f"\n### MOTOR: {nombre}\n{texto}")
    bloques.append("\nJunta todo y contesta a Mj con una sola voz, siguiendo tus reglas.")
    return "\n".join(bloques)


NEGATIVAS_DEFECTO = [
    r"no se puede", r"no es posible", r"no puedo", r"imposible", r"no tengo acceso",
    r"no me es posible", r"no est[aá] a mi alcance", r"no hay forma",
    r"i can(no|')?t", r"cannot", r"not possible", r"unable to", r"i don'?t have access",
]


def patrones_negativa():
    crudo = env("NEGATIVAS_REGEX")  # lista separada por "||"
    lista = crudo.split("||") if crudo else NEGATIVAS_DEFECTO
    return [re.compile(p, re.IGNORECASE) for p in lista if p.strip()]


def es_negativa(texto):
    return any(p.search(texto or "") for p in patrones_negativa())


def rotar(motores, ciclo):
    if not motores:
        return motores
    k = ciclo % len(motores)
    return motores[k:] + motores[:k]


def pedido_resolucion(pregunta, borrador, lider, ciclo):
    return (f"CICLO DE RESOLUCIÓN {ciclo}. Lidera: {lider}.\n"
            f"Mj pidió:\n{pregunta}\n\nEl borrador anterior se negó:\n{borrador}\n\n"
            "Prohibido negarse. Encuentra el camino que SÍ funciona: la solución directa, un análogo "
            "o un equivalente funcional legítimo. Si de verdad hay un bloqueo, nómbralo concreto y da "
            "la ÚNICA acción que Mj tendría que aceptar, en una línea que empiece con 'ACCION:'.")


def resolver(pregunta, historial, prompt, motores=None):
    """Gestiona y, si el borrador se niega, corre hasta N ciclos rotando el motor líder.
    Devuelve (texto, motores, bloqueado, ciclos)."""
    motores = motores_config() if motores is None else motores
    texto, resp = gestionar(pregunta, historial, prompt, motores)
    maximo = int(env("CICLOS_MAX", "3"))
    ciclo = 0
    # (e) si la pregunta de Mj contiene "no se puede", no activar ciclo
    if "no se puede" in (pregunta or "").lower():
        return texto, resp, es_negativa(texto), ciclo
    while es_negativa(texto) and ciclo < maximo:
        ciclo += 1
        orden = rotar(motores, ciclo)
        lider = orden[0]["nombre"] if orden else "gestor"
        texto, resp = gestionar(pedido_resolucion(pregunta, texto, lider, ciclo), historial, prompt, orden)
    return texto, resp, es_negativa(texto), ciclo


def accion_de(texto):
    m = re.search(r"ACCION:\s*(.+)", texto or "")
    return m.group(1).strip() if m else "Aceptar el camino propuesto arriba."


def gestionar(pregunta, historial, prompt, motores=None):
    respuestas = consultar_motores(pregunta, historial, motores)
    validas = {k: v for k, v in respuestas.items() if not v.startswith("ERROR:")}
    key = env("GESTOR_API_KEY_ENV", "GROQ_API_KEY")
    gk = env(key)
    if not gk:
        if validas:
            return next(iter(validas.values())), respuestas
        return "No hay ningún motor con clave. Pon GROQ_API_KEY o GEMINI_API_KEY en el .env.", respuestas
    gestor = {"nombre": "gestor", "tipo": env("GESTOR_TIPO", "groq"),
              "model": env("GESTOR_MODEL", "openai/gpt-oss-120b"), "key": gk}
    messages = [{"role": "system", "content": prompt}] + historial + [
        {"role": "user", "content": entrada_gestor(pregunta, respuestas)}]
    try:
        return llamar_motor(gestor, messages), respuestas
    except Exception as e:
        # (b) reintento con espera y respaldo en 429
        if "429" in str(e) or "rate" in str(e).lower() or "tpm" in str(e).lower():
            time.sleep(2)
            respaldo = env("GESTOR_MODEL_RESPALDO", "openai/gpt-oss-20b")
            gestor["model"] = respaldo
            try:
                return llamar_motor(gestor, messages), respuestas
            except Exception as e2:
                e = e2
        if validas:
            n, t = next(iter(validas.items()))
            return f"(El gestor falló; te paso la respuesta de {n}.)\n\n{t}", respuestas
        return f"Ningún motor respondió ({type(e).__name__}). Reintenta en un minuto.", respuestas


# ---------- memoria y bitácora ----------

def ruta_datos():
    p = Path(env("BOT_DATA_DIR", str(AQUI / "datos")))
    p.mkdir(parents=True, exist_ok=True)
    return p


def cargar_memoria():
    f = ruta_datos() / "memoria.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def guardar_memoria(mem):
    f = ruta_datos() / "memoria.json"
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(mem, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(f)


def recordar(mem, chat_id, pregunta, respuesta, n=None):
    n = n or int(env("MEMORIA_TURNOS", "6"))
    h = mem.setdefault(str(chat_id), [])
    h += [{"role": "user", "content": pregunta}, {"role": "assistant", "content": respuesta}]
    mem[str(chat_id)] = h[-2 * n:]


def bitacora(registro):
    with open(ruta_datos() / "turnos.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


# ---------- comandos portados de telegram-bot ----------

def leer_local(ruta, max_chars=3500):
    try:
        texto = Path(ruta).read_text(encoding="utf-8"))
    except OSError:
        return None
    if len(texto) > max_chars:
        texto = texto[:max_chars] + "\n\n...(recortado)"
    return texto


def ultimos_eventos(n=5):
    try:
        archivos = sorted(BUS.glob("*.json"), key=lambda p: p.stat().st_mtime)[-n:]
    except OSError:
        return []
    eventos = []
    for p in archivos:
        try:
            eventos.append(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    return eventos


def aplicar_emitir(texto):
    """Aplica bloque [EMITIR] localmente. Devuelve (ok, eid_o_error)."""
    m = re.search(r"\[EMITIR\](.*?)\[/EMITIR\]", texto, re.S)
    if not m:
        return False, "No se encontró bloque [EMITIR]...[/EMITIR]."
    campos = {}
    for linea in m.group(1).strip().splitlines():
        if ":" in linea:
            k, v = linea.split(":", 1)
            campos[k.strip().lower()] = v.strip()
    de = campos.get("de", "")
    tipo = campos.get("tipo", "")
    mensaje = campos.get("mensaje", "")
    if not de or tipo not in TIPOS_EMITIR or not mensaje:
        return False, f"Bloque inválido: necesita de, tipo ({', '.join(TIPOS_EMITIR)}) y mensaje."
    BUS.mkdir(parents=True, exist_ok=True)
    ahora = datetime.datetime.now()
    eid = ahora.strftime("%Y%m%d-%H%M%S-%f")
    evento = {
        "formato": 1,
        "id": eid,
        "fecha": ahora.strftime("%Y-%m-%d %H:%M"),
        "version": 0,
        "de": de,
        "tipo": tipo,
        "mensaje": mensaje,
    }
    (BUS / f"{eid}.json").write_text(json.dumps(evento, ensure_ascii=False, indent=2), encoding="utf-8")
    return True, eid


def subir_evento_github(eid):
    """Sube el evento a main vía API de GitHub si hay GITHUB_TOKEN. Nunca pone el token en el repo."""
    token = env("GITHUB_TOKEN") or env("GH_TOKEN")
    if not token:
        return False
    path = f"conector/bus/{eid}.json"
    contenido = (BUS / f"{eid}.json").read_text(encoding="utf-8")
    url = f"https://api.github.com/repos/marcojpad-hash/agente-cero-costo/contents/{path}"
    payload = {
        "message": f"Bus: evento {eid} emitido por Telegram",
        "content": __import__("base64").b64encode(contenido.encode()).decode(),
        "branch": "main",
    }
    try:
        # Primero intenta obtener SHA si existe (no debería)
        req = urllib.request.Request(url, headers={"Authorization": f"token {token}", "User-Agent": "bot-gestor/1.0"})
        try:
            with urllib.request.urlopen(req) as r:
                existente = json.loads(r.read())
                payload["sha"] = existente["sha"]
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers={
            "Authorization": f"token {token}",
            "User-Agent": "bot-gestor/1.0",
            "Content-Type": "application/json",
        }, method="PUT")
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status in (200, 201)
    except Exception:
        return False


def cmd_memoria():
    d = leer_local(DIGEST)
    return d or "No hay resumen de memoria local todavía."


def cmd_bus():
    eventos = ultimos_eventos()
    if not eventos:
        return "El bus no tiene eventos todavía."
    lineas = ["Últimos eventos del bus:\n"]
    for e in eventos:
        lineas.append(f"- {e.get('fecha','')} [{e.get('tipo','')}] {e.get('de','')}: {e.get('mensaje','')}")
    return "\n".join(lineas)


def cmd_interpretar(texto, prompt):
    """Interpreta texto de otro modelo usando Groq (User-Agent propio)."""
    key = env("GROQ_API_KEY")
    if not key:
        return "Falta GROQ_API_KEY para interpretar."
    messages = [
        {"role": "system", "content": prompt or "Interpreta y unifica el texto en una sola voz clara en español."},
        {"role": "user", "content": "Texto a interpretar:\n" + texto[:4000]},
    ]
    try:
        return _openai_chat(GROQ_CHAT, key, env("GESTOR_MODEL", "openai/gpt-oss-120b"), messages, 60)
    except Exception as e:
        return f"No pude interpretar ({type(e).__name__}): {str(e)[:200]}"


# ---------- telegram ----------

def partir(texto, limite=TG_LIMITE):
    texto = texto or "(vacío)"
    partes = []
    while len(texto) > limite:
        corte = texto.rfind("\n", 0, limite)
        if corte < limite // 2:
            corte = texto.rfind(" ", 0, limite)
        if corte < limite // 2:
            corte = limite
        partes.append(texto[:corte])
        texto = texto[corte:].lstrip("\n")
    partes.append(texto)
    return partes


def tg(token, metodo, payload=None, timeout=70):
    return http_json(TG_API.format(token=token, method=metodo), payload or {}, timeout=timeout)


def enviar(token, chat_id, texto, botones=None):
    partes = partir(texto)
    for i, p in enumerate(partes):
        payload = {"chat_id": chat_id, "text": p}
        if botones and i == len(partes) - 1:
            payload["reply_markup"] = {"inline_keyboard": [botones]}
        try:
            tg(token, "sendMessage", payload)
        except Exception:
            # No tumbar el bot ni los tests por fallo de red/token de prueba
            pass


def botones_decision(turno):
    return [{"text": "Acepto", "callback_data": f"si:{turno}"},
            {"text": "No", "callback_data": f"no:{turno}"}]


def atender_boton(token, cq):
    """Registra la decisión de Mj al tocar Acepto/No."""
    chat_id = cq.get("message", {}).get("chat", {}).get("id")
    quien = cq.get("from", {}).get("id")
    if not (permitido(chat_id) and permitido(quien)):
        tg(token, "answerCallbackQuery", {"callback_query_id": cq["id"]})
        return None
    voto, _, turno = (cq.get("data") or "").partition(":")
    acepto = voto == "si"
    bitacora({"ts": time.time(), "chat": chat_id, "turno": turno, "decision_mj": "acepto" if acepto else "no",
              "atribucion": "lo hizo el bot" if acepto else None})
    tg(token, "answerCallbackQuery", {"callback_query_id": cq["id"],
                                      "text": "Anotado: lo hizo el bot." if acepto else "Anotado: no."})
    return "acepto" if acepto else "no"


def transcribir_voz(token, file_id):
    key = env("GROQ_API_KEY")
    if not key:
        raise RuntimeError("falta GROQ_API_KEY para transcribir la voz")
    info = tg(token, "getFile", {"file_id": file_id})
    audio = http_bytes(TG_FILE.format(token=token, path=info["result"]["file_path"]))
    limite = "----bot" + uuid.uuid4().hex
    def campo(n, v):
        return (f"--{limite}\r\nContent-Disposition: form-data; name=\"{n}\"\r\n\r\n{v}\r\n").encode()
    cuerpo = (campo("model", env("WHISPER_MODEL", "whisper-large-v3-turbo")) + campo("language", "es")
              + f"--{limite}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"voz.ogg\"\r\nContent-Type: audio/ogg\r\n\r\n".encode() + audio + f"\r\n--{limite}--\r\n".encode())
    req = urllib.request.Request(GROQ_AUDIO, data=cuerpo, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": f"multipart/form-data; boundary={limite}",
        "User-Agent": "bot-gestor/1.0",
    })
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())["text"].strip()


def resumen_estado(prompt):
    motores = motores_config()
    lineas = [f"Motores activos: {len(motores)}"]
    for m in motores:
        lineas.append(f"- {m['nombre']} ({m['model']})")
    lineas.append(f"Prompt: {len(prompt)} caracteres")
    return "\n".join(lineas)


def atender(token, update, prompt, mem):
    """Procesa un update. Devuelve la respuesta enviada o None.
    Acepta tanto un update completo de Telegram como un dict mensaje-like (con 'chat').
    Cuando hay bloqueo con botones, devuelve un dict con la clave 'botones'.
    """
    if "callback_query" in update:
        return atender_boton(token, update["callback_query"])
    msg = update.get("message") or update.get("edited_message") or (update if isinstance(update, dict) and "chat" in update else {})
    chat_id = msg.get("chat", {}).get("id")
    if not permitido(chat_id):
        return None
    texto = msg.get("text") or ""
    if msg.get("voice") or msg.get("audio"):
        archivo = (msg.get("voice") or msg.get("audio"))["file_id"]
        try:
            texto = transcribir_voz(token, archivo)
        except Exception as e:
            return f"No pude transcribir tu nota de voz ({type(e).__name__}). Mándamela otra vez o escríbela."
    if not texto:
        return None
    if texto.startswith("/memoria"):
        return cmd_memoria()
    if texto.startswith("/bus"):
        return cmd_bus()
    if texto.startswith("/interpretar"):
        return cmd_interpretar(texto[len("/interpretar"):].strip(), prompt)
    if "[EMITIR]" in texto and "[/EMITIR]" in texto:
        ok, eid = aplicar_emitir(texto)
        if ok:
            subido = subir_evento_github(eid)
            return f"Evento {eid} creado." + (" subido a GitHub." if subido else "")
        return eid
    if texto.startswith("/estado"):
        return resumen_estado(prompt)
    respuesta, motores, bloqueado, ciclos = resolver(texto, mem.get(str(chat_id), []), prompt)
    recordar(mem, chat_id, texto, respuesta)
    guardar_memoria(mem)
    turno = uuid.uuid4().hex[:8]
    bitacora({"ts": time.time(), "chat": chat_id, "turno": turno, "pregunta": texto[:200],
              "respuesta": respuesta[:500], "bloqueado": bloqueado, "ciclos": ciclos,
              "motores": list(motores.keys())})
    botones = botones_decision(turno) if bloqueado else None
    enviar(token, chat_id, respuesta, botones)
    if botones:
        return {"texto": respuesta, "botones": botones}
    return respuesta


def main():
    token = env("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("falta TELEGRAM_BOT_TOKEN")
    prompt = cargar_prompt()
    mem = cargar_memoria()
    offset = None
    while True:
        try:
            ups = tg(token, "getUpdates", {"offset": offset, "timeout": 50}, timeout=70)
            for u in ups.get("result", []):
                offset = u["update_id"] + 1
                atender(token, u, prompt, mem)
        except Exception as e:
            print(f"error en loop: {e}", file=sys.stderr)
            time.sleep(5)


if __name__ == "__main__":
    main()
