#!/usr/bin/env python3
"""Bot de Telegram: el host en línea del equipo.

No necesita un servidor público ni puertos de entrada: Telegram se
consulta por polling (salida HTTPS a api.telegram.org), así que corre
en la VM de Pecas. Es el host que los modelos pueden alcanzar: lee el
estado, la memoria y el bus, y acepta bloques [EMITIR] para escribir
en el bus.

El token va por variable de entorno TELEGRAM_BOT_TOKEN (nunca en el
repo, nunca en el chat; se guarda en la bóveda).

Comandos:
  /start, /ayuda  - qué hace el bot
  /estado         - estado vigente del equipo
  /memoria        - resumen público de la memoria
  /bus            - últimos eventos del bus
  [EMITIR]...[/EMITIR] - emite un evento al bus (lo aplica y lo sube)

Uso:
    TELEGRAM_BOT_TOKEN=... python3 bot.py
"""
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CONECTOR = os.path.join(REPO, "conector")
BUS = os.path.join(CONECTOR, "bus")
APLICAR = os.path.join(CONECTOR, "aplicar.py")
DIGEST = os.path.join(REPO, "memoria-digest", "DIGEST.md")
ESTADO = os.path.join(CONECTOR, "ESTADO.md")
GITHUB_CLI = "/opt/hatch/bin/github"
LIMITE = 4000  # Telegram permite 4096 por mensaje


def log(*args):
    print(time.strftime("%Y-%m-%d %H:%M:%S"), *args, flush=True)


def leer(ruta, max_chars=LIMITE):
    try:
        with open(ruta, encoding="utf-8") as f:
            texto = f.read()
    except OSError:
        return None
    if len(texto) > max_chars:
        texto = texto[:max_chars] + "\n\n...(recortado, el archivo completo está en el repo)"
    return texto


def api(token, metodo, **params):
    url = f"https://api.telegram.org/bot{token}/{metodo}"
    data = urllib.parse.urlencode(params).encode() if params else None
    req = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def enviar(token, chat_id, texto):
    # Parte en trozos si es muy largo.
    for i in range(0, len(texto), LIMITE):
        api(token, "sendMessage", chat_id=chat_id,
            text=texto[i:i + LIMITE])


def ultimos_eventos(n=5):
    try:
        archivos = sorted(os.listdir(BUS))
    except OSError:
        return []
    eventos = []
    for nombre in archivos[-n:]:
        if not nombre.endswith(".json"):
            continue
        try:
            with open(os.path.join(BUS, nombre), encoding="utf-8") as f:
                eventos.append(json.load(f))
        except (OSError, ValueError):
            continue
    return eventos


def subir_evento(eid):
    """Sube el evento y el estado a GitHub. Devuelve True si quedó."""
    rutas = [
        f"conector/bus/{eid}.json",
        "conector/ESTADO.md",
        "conector/estado.json",
        "avisos/VERSION",
        "avisos/ACTUALIZACIONES.md",
    ]
    paths_file = os.path.join(HERE, ".push-paths.txt")
    with open(paths_file, "w", encoding="utf-8") as f:
        for r in rutas:
            f.write(r + "\0")
    try:
        r = subprocess.run(
            [GITHUB_CLI, "push-files",
             "--source-dir", REPO,
             "--paths-file", paths_file,
             "--owner", "marcojpad-hash",
             "--repo", "agente-cero-costo",
             "--branch", "main",
             "--message", f"Bus: evento {eid} emitido por Telegram"],
            capture_output=True, text=True, timeout=120)
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False
    finally:
        try:
            os.remove(paths_file)
        except OSError:
            pass


def aplicar_bloque(texto):
    """Aplica un bloque [EMITIR] con aplicar.py. Devuelve (ok, salida)."""
    try:
        r = subprocess.run(
            [sys.executable, APLICAR],
            input=texto, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, str(e)
    if r.returncode != 0:
        return False, (r.stdout + r.stderr).strip() or "falló aplicar.py"
    return True, r.stdout.strip()


AYUDA = (
    "Soy el host del equipo. Comandos:\n"
    "/estado - estado vigente\n"
    "/memoria - resumen público de la memoria\n"
    "/bus - últimos eventos del bus\n"
    "Para emitir, mándame el bloque:\n"
    "[EMITIR]\n"
    "de: <tu nombre>\n"
    "tipo: actualizacion\n"
    "mensaje: <lo nuevo, en una línea>\n"
    "[/EMITIR]"
)


def responder(token, chat_id, texto):
    if "[EMITIR]" in texto and "[/EMITIR]" in texto:
        ok, salida = aplicar_bloque(texto)
        if not ok:
            enviar(token, chat_id, f"No se pudo aplicar el bloque:\n{salida}")
            return
        # El id del evento viene en la salida: "Aplicado: <id> (v..)".
        eid = ""
        for linea in salida.splitlines():
            if linea.startswith("Aplicado:"):
                eid = linea.split(":", 1)[1].strip().split(" ")[0]
        subido = subir_evento(eid) if eid else False
        if subido:
            enviar(token, chat_id,
                   f"Evento {eid} en el bus y subido a GitHub.")
        else:
            enviar(token, chat_id,
                   f"Evento {eid} guardado en el bus. La subida a "
                   f"GitHub quedó pendiente (se sube en el siguiente "
                   f"paso de Pecas).")
        return
    cmd = texto.strip().split()[0].lower() if texto.strip() else ""
    if cmd in ("/start", "/ayuda", "/help"):
        enviar(token, chat_id, AYUDA)
    elif cmd == "/estado":
        estado = leer(ESTADO)
        enviar(token, chat_id, estado or "No hay estado local todavía.")
    elif cmd == "/memoria":
        digest = leer(DIGEST)
        enviar(token, chat_id, digest or "No hay resumen de memoria todavía.")
    elif cmd == "/bus":
        eventos = ultimos_eventos()
        if not eventos:
            enviar(token, chat_id, "El bus no tiene eventos todavía.")
            return
        lineas = ["Últimos eventos del bus:\n"]
        for e in eventos:
            lineas.append(f"- {e.get('fecha','')} [{e.get('tipo','')}] "
                          f"{e.get('de','')}: {e.get('mensaje','')}")
        enviar(token, chat_id, "\n".join(lineas))
    else:
        enviar(token, chat_id,
               "No entendí. Usa /ayuda para ver los comandos, o "
               "mándame un bloque [EMITIR] para emitir al bus.")


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("Falta TELEGRAM_BOT_TOKEN (nunca va en el repo ni en el chat).")
        sys.exit(1)
    log("Bot arrancado. Polling a Telegram...")
    offset = 0
    while True:
        try:
            resp = api(token, "getUpdates", offset=offset, timeout=30)
        except Exception as e:  # noqa: BLE001 - el polling debe seguir
            log("Error de polling, reintentando:", e)
            time.sleep(5)
            continue
        if not resp.get("ok"):
            log("Respuesta no ok:", resp)
            time.sleep(5)
            continue
        for upd in resp.get("result", []):
            offset = upd["update_id"] + 1
            msg = upd.get("message") or {}
            texto = msg.get("text", "")
            chat = msg.get("chat", {})
            if not texto or not chat.get("id"):
                continue
            log(f"Mensaje de {chat.get('id')}: {texto[:80]!r}")
            try:
                responder(token, chat["id"], texto)
            except Exception as e:  # noqa: BLE001 - un mensaje no tumba el bot
                log("Error respondiendo:", e)
                try:
                    enviar(token, chat["id"],
                           "Me atoré respondiendo eso. Prueba /ayuda.")
                except Exception:
                    pass


if __name__ == "__main__":
    main()
