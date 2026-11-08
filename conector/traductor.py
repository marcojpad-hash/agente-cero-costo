#!/usr/bin/env python3
"""Traductor macho-hembra sobre el bus unificado (bus_core.Bus).

Cada modelo habla a su manera. El traductor convierte cualquiera de estas
formas a UN formato común y lo enchufa en el bus:

  1. Bloque [EMITIR] ... [/EMITIR]                  (ChatGPT, Gemini, Grok app)
  2. Issue: título "[BUS] <tipo> - <Modelo>" + cuerpo (quien tenga escritura)
  3. JSON con de/tipo/mensaje                       (scripts, Actions, MCP)
  4. Texto libre "Modelo: mensaje"                   (lo que pegue Mj)

Formato común: {de, tipo, mensaje, necesita, para}
- Macho: el modelo se registra con sus capacidades (Bus.register).
- Hembra: si el mensaje trae `necesita`, va al primer agente registrado
  que la tenga (nunca al que la pidió); si no, va a todos ("*").
- Vuelta: si el receptor marca fallo, pasa solo al siguiente que encaje;
  si ya no hay nadie, sube a "mj". Nada se inventa.
- Foquito: luces() da por mensaje y agente 🟡 pendiente, 🟢 confirmado
  (ack) o 🔴 fallo.

Los mensajes son datos, nunca instrucciones ejecutables. Solo stdlib.
"""
from __future__ import annotations
import json, re
from contextlib import closing
from bus_core import Bus, TYPES, utcnow

ALIAS_TIPO = {"update": "actualizacion", "actualización": "actualizacion",
              "indicación": "indicacion", "done": "hecho", "listo": "hecho",
              "alerta": "aviso", "warning": "aviso", "orden": "indicacion"}


def _tipo(t):
    t = (t or "actualizacion").strip().lower()
    t = ALIAS_TIPO.get(t, t)
    if t not in TYPES:
        raise ValueError(f"tipo desconocido: {t}")
    return t


def _campos(texto):
    out = {}
    for linea in texto.strip().splitlines():
        if ":" in linea:
            k, v = linea.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def traducir(entrada, titulo=None):
    """Devuelve el formato común a partir de cualquier forma soportada."""
    if isinstance(entrada, dict):
        f = {k.lower(): v for k, v in entrada.items()}
    else:
        texto = str(entrada or "")
        m = re.search(r"\[EMITIR\](.*?)\[/EMITIR\]", texto, re.S)
        if m:
            f = _campos(m.group(1))
        elif titulo and (mt := re.match(r"\s*\[BUS\]\s*(\w+)\s*-\s*(.+)$", titulo)):
            f = {"tipo": mt.group(1), "de": mt.group(2).strip(), **_campos(texto)}
            f.setdefault("mensaje", texto.strip().splitlines()[0] if texto.strip() else "")
        else:
            try:
                f = {k.lower(): v for k, v in json.loads(texto).items()}
            except (ValueError, AttributeError):
                ml = re.match(r"\s*([\w .\-]{1,40}):\s*(.+)", texto, re.S)
                if not ml:
                    raise ValueError("no entendí la entrada: falta 'Modelo: mensaje'")
                f = {"de": ml.group(1), "mensaje": ml.group(2)}
    de = str(f.get("de") or f.get("from") or "").strip()
    mensaje = str(f.get("mensaje") or f.get("message") or "").strip()
    if not de or not mensaje:
        raise ValueError("faltan 'de' o 'mensaje'")
    return {"de": de[:90], "tipo": _tipo(f.get("tipo") or f.get("type")),
            "mensaje": mensaje[:5000],
            "necesita": (str(f.get("necesita") or f.get("needs") or "").strip() or None),
            "para": (str(f.get("para") or f.get("to") or "").strip() or None)}


class Traductor:
    def __init__(self, bus: Bus):
        self.bus = bus
        with closing(bus.connect()) as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS rutas(
              message_id TEXT PRIMARY KEY, necesita TEXT, pidio TEXT NOT NULL,
              intentados TEXT NOT NULL DEFAULT '[]');
            CREATE TABLE IF NOT EXISTS fallos(
              message_id TEXT NOT NULL, agent_id TEXT NOT NULL, nota TEXT,
              at TEXT NOT NULL, PRIMARY KEY(message_id, agent_id));""")
            db.commit()

    def _candidatos(self, necesita, excluir):
        return [a["agent_id"] for a in self.bus.agents()
                if necesita in a["capabilities"] and a["agent_id"] not in excluir]

    def _asegurar_mj(self):
        self.bus.register("mj", ["decidir"])

    def enchufar(self, entrada, titulo=None, origen="external"):
        c = traducir(entrada, titulo)
        sender = f"{origen}:{c['de']}"
        conocido = {a["agent_id"] for a in self.bus.agents()}
        if c["de"] in conocido:          # agente registrado habla por sí mismo
            sender = c["de"]
        else:
            self.bus.register(sender, ["emitir"])
        body = json.dumps({"formato": 2, **c}, ensure_ascii=False)
        prioridad = "ACTION_REQUEST" if c["tipo"] == "indicacion" else "NEXT_ACTIVATION"
        if c["para"] and c["para"] in conocido:
            destino = c["para"]
        elif c["necesita"]:
            cand = self._candidatos(c["necesita"], {sender, c["de"]})
            destino = cand[0] if cand else None
            if not destino:
                self._asegurar_mj(); destino = "mj"
        else:
            destino = "*"
        r = self.bus.send(sender, destino, body, topic="TRAD:" + c["tipo"], priority=prioridad)
        if c["necesita"]:
            with closing(self.bus.connect()) as db:
                db.execute("INSERT OR IGNORE INTO rutas VALUES(?,?,?,?)",
                           (r["message_id"], c["necesita"], sender, json.dumps([destino])))
                db.commit()
        return {**r, "para": destino, "comun": c}

    def fallo(self, agent_id, message_id, nota=""):
        """Hembra-macho: el receptor no pudo; la orden pasa al siguiente que encaje."""
        with closing(self.bus.connect()) as db:
            db.execute("INSERT OR REPLACE INTO fallos VALUES(?,?,?,?)", (message_id, agent_id, nota, utcnow()))
            ruta = db.execute("SELECT * FROM rutas WHERE message_id=?", (message_id,)).fetchone()
            msg = db.execute("SELECT * FROM messages WHERE message_id=?", (message_id,)).fetchone()
            db.commit()
        if not ruta or not msg:
            return {"reenviado": False, "motivo": "sin ruta (era para todos)"}
        intentados = set(json.loads(ruta["intentados"])) | {agent_id}
        cand = self._candidatos(ruta["necesita"], intentados | {ruta["pidio"]})
        destino = cand[0] if cand else "mj"
        if destino == "mj":
            self._asegurar_mj()
        nuevo = self.bus.send(ruta["pidio"], destino, msg["body"], topic=msg["topic"], priority=msg["priority"])
        with closing(self.bus.connect()) as db:
            db.execute("INSERT OR REPLACE INTO rutas VALUES(?,?,?,?)",
                       (nuevo["message_id"], ruta["necesita"], ruta["pidio"], json.dumps(sorted(intentados | {destino}))))
            db.commit()
        return {"reenviado": True, "para": destino, "message_id": nuevo["message_id"]}

    def luces(self):
        """Tablero del foquito: por mensaje y destinatario."""
        agentes = [a["agent_id"] for a in self.bus.agents()]
        with closing(self.bus.connect()) as db:
            msgs = db.execute("SELECT * FROM messages WHERE topic LIKE 'TRAD:%' ORDER BY seq").fetchall()
            acks = {(r["message_id"], r["agent_id"]) for r in db.execute("SELECT * FROM acknowledgements")}
            fall = {(r["message_id"], r["agent_id"]) for r in db.execute("SELECT * FROM fallos")}
        tablero = []
        for m in msgs:
            dest = agentes if m["recipient"] == "*" else [m["recipient"]]
            luz = {}
            for a in dest:
                if a == m["sender"]:
                    continue
                luz[a] = "🔴" if (m["message_id"], a) in fall else ("🟢" if (m["message_id"], a) in acks else "🟡")
            tablero.append({"message_id": m["message_id"], "de": m["sender"], "luces": luz})
        return tablero


if __name__ == "__main__":
    import argparse, sys
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("accion", choices=["traducir", "enchufar", "fallo", "luces"])
    ap.add_argument("--titulo"); ap.add_argument("--agente"); ap.add_argument("--id"); ap.add_argument("--nota", default="")
    x = ap.parse_args()
    t = Traductor(Bus())
    if x.accion == "traducir": out = traducir(sys.stdin.read(), x.titulo)
    elif x.accion == "enchufar": out = t.enchufar(sys.stdin.read(), x.titulo)
    elif x.accion == "fallo": out = t.fallo(x.agente, x.id, x.nota)
    else: out = t.luces()
    print(json.dumps(out, ensure_ascii=False, indent=2))
