#!/usr/bin/env python3
"""Bot gestor de Telegram: un solo bot que habla por todos los motores.

Telegram (long polling) -> motores gratis en paralelo -> gestor final
(system prompt de PROMPT_GESTOR.md) -> una sola respuesta.

Solo stdlib. Las claves se leen SOLO de variables de entorno.
Un motor sin clave se salta; no tumba al bot.
"""
import json
import os
import sys
import time
import uuid
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

AQUI = Path(__file__).resolve().parent
GROQ_CHAT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_AUDIO = "https://api.groq.com/openai/v1/audio/transcriptions"
OPENROUTER_CHAT = "https://openrouter.ai/api/v1/chat/completions"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
TG_API = "https://api.telegram.org/bot{token}/{method}"
TG_FILE = "https://api.telegram.org/file/bot{token}/{path}"
ESTADO_URL = "https://raw.githubusercontent.com/marcojpad-hash/agente-cero-costo/main/conector/ESTADO.md"
TG_LIMITE = 4096


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
        ("groq-2", "GROQ_API_KEY", "groq", env("MOTOR_GROQ2_MODEL", "llama-3.3-70b-versatile")),
        ("gemini", "GEMINI_API_KEY", "gemini", env("MOTOR_GEMINI_MODEL", "gemini-2.5-flash")),
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
    messages = [{"role": "system", "content":
                 "Responde en español de México, directo y concreto. No inventes datos ni fuentes; "
                 "si no sabes algo, dilo y da el camino que sí funciona."}]
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
        bloques.append(f"\n### MOTOR: {nombre}\n{texto}")
    bloques.append("\nJunta todo y contesta a Mj con una sola voz, siguiendo tus reglas.")
    return "\n".join(bloques)


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


def enviar(token, chat_id, texto):
    for p in partir(texto):
        tg(token, "sendMessage", {"chat_id": chat_id, "text": p})


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
              + f"--{limite}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"voz.ogg\"\r\n"
                "Content-Type: audio/ogg\r\n\r\n".encode() + audio + f"\r\n--{limite}--\r\n".encode())
    req = urllib.request.Request(GROQ_AUDIO, data=cuerpo, headers={
        "Authorization": f"Bearer {key}", "Content-Type": f"multipart/form-data; boundary={limite}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())["text"].strip()


def resumen_estado(prompt):
    texto = http_bytes(ESTADO_URL, timeout=30).decode("utf-8", "replace")
    pedido = "Resume para Mj, en 5 líneas máximo, este estado del equipo:\n\n" + texto[:12000]
    resp, _ = gestionar(pedido, [], prompt, motores=[])
    return resp if env("GROQ_API_KEY") else texto[:3500]


def atender(token, msg, prompt, mem):
    chat_id = msg["chat"]["id"]
    if not permitido(chat_id):
        bitacora({"ts": time.time(), "chat": chat_id, "rechazado": True})
        return None
    texto = (msg.get("text") or "").strip()
    if msg.get("voice") or msg.get("audio"):
        archivo = (msg.get("voice") or msg.get("audio"))["file_id"]
        try:
            texto = transcribir_voz(token, archivo)
        except Exception as e:
            return f"No pude transcribir tu nota de voz ({type(e).__name__}). Mándamela otra vez o escríbela."
    if not texto:
        return None
    cmd = texto.split()[0].split("@")[0].lower()
    if cmd == "/start":
        return "Listo, Mj. Háblame o mándame voz. Comandos: /motores /estado /reset"
    if cmd == "/motores":
        ms = motores_config()
        return "Motores prendidos:\n" + ("\n".join(f"• {m['nombre']} ({m['model']})" for m in ms)
                                         or "ninguno: falta poner claves en el .env")
    if cmd == "/reset":
        mem.pop(str(chat_id), None)
        guardar_memoria(mem)
        return "Memoria de este chat borrada."
    if cmd == "/estado":
        try:
            return resumen_estado(prompt)
        except Exception as e:
            return f"No pude leer ESTADO.md ({type(e).__name__}): {ESTADO_URL}"
    t0 = time.time()
    respuesta, motores = gestionar(texto, mem.get(str(chat_id), []), prompt)
    recordar(mem, chat_id, texto, respuesta)
    guardar_memoria(mem)
    bitacora({"ts": t0, "seg": round(time.time() - t0, 1), "chat": chat_id, "pregunta": texto,
              "motores": {k: v[:2000] for k, v in motores.items()}, "respuesta": respuesta})
    return respuesta


def main():
    token = env("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("falta TELEGRAM_BOT_TOKEN")
    if not chats_permitidos():
        raise SystemExit("falta TELEGRAM_ALLOWED_CHAT_IDS: sin eso el bot no le contesta a nadie")
    prompt = cargar_prompt()
    mem = cargar_memoria()
    print("bot gestor arriba; motores:", [m["nombre"] for m in motores_config()], flush=True)
    offset = 0
    while True:
        try:
            r = tg(token, "getUpdates", {"offset": offset, "timeout": 50,
                                         "allowed_updates": ["message"]})
            for u in r.get("result", []):
                offset = u["update_id"] + 1
                msg = u.get("message")
                if not msg:
                    continue
                resp = atender(token, msg, prompt, mem)
                if resp:
                    enviar(token, msg["chat"]["id"], resp)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("error en el ciclo:", type(e).__name__, str(e)[:200], file=sys.stderr, flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
