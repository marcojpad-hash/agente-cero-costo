#!/usr/bin/env python3
"""Recibir: el enchufe hembra del conector.

Lee el bus compartido (conector/bus/) y entrega solo los eventos
nuevos desde la última lectura, usando un watermark local (qué ya vio
este receptor). Después de entregarlos, guarda el watermark nuevo.
Con --solo-ver no lo guarda: solo mira qué hay nuevo.

El watermark es un conjunto de ids vistos (no un solo último id):
el bus mezcla dos formatos de id (los locales `20261108-...` de
emitir.py y los de GitHub `gh-issue-N` del workflow
github-native-agent-bus.yml), y comparar por orden alfabético entre
formatos se salta eventos. Con el conjunto, cada evento se entrega
una sola vez, venga del transporte que venga.

El watermark es local de cada máquina/receptor (por defecto
~/.cache/agente-cero-costo/visto.json) y nunca va en el repo: cada
modelo tiene su propio "qué ya vi". El bus sí es compartido (viaja
con el repo).

El par es reversible: cualquier modelo puede emitir (emitir.py) y
cualquier modelo puede recibir (este script). El que recibe hoy puede
emitir mañana, y viceversa.

Uso:
    python3 recibir.py [--visto RUTA] [--solo-ver]
"""
import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BUS = os.path.join(HERE, "bus")
VISTO_DEF = os.path.expanduser("~/.cache/agente-cero-costo/visto.json")
MAX_VISTOS = 500


def cargar_vistos(ruta):
    """Conjunto de ids ya vistos. Acepta el formato viejo
    {"ultimo_id": ...} y lo migra a un conjunto de un elemento."""
    try:
        data = json.load(open(ruta, encoding="utf-8"))
    except (OSError, ValueError, AttributeError):
        return set()
    if isinstance(data, dict):
        if isinstance(data.get("vistos"), list):
            return set(data["vistos"])
        if data.get("ultimo_id"):
            return {data["ultimo_id"]}
    return set()


def guardar_vistos(ruta, vistos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    recorte = sorted(vistos)[-MAX_VISTOS:]
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump({"vistos": recorte}, f)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--visto", default=VISTO_DEF)
    parser.add_argument("--solo-ver", action="store_true")
    args = parser.parse_args()
    vistos = cargar_vistos(args.visto)
    eventos = []
    if os.path.isdir(BUS):
        for nombre in sorted(os.listdir(BUS)):
            if not nombre.endswith(".json"):
                continue
            try:
                ev = json.load(open(os.path.join(BUS, nombre),
                                    encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if ev.get("id") and ev["id"] not in vistos:
                eventos.append(ev)
    if not eventos:
        print("Sin novedades: no hay eventos nuevos en el bus.")
        return
    print(f"Eventos nuevos: {len(eventos)}")
    for ev in eventos:
        print(f"- {ev.get('fecha')} (v{ev.get('version')}, "
              f"{ev.get('tipo')}, de {ev.get('de')}): {ev.get('mensaje')}")
    if not args.solo_ver:
        vistos.update(ev["id"] for ev in eventos)
        guardar_vistos(args.visto, vistos)
        print(f"Watermark guardado: {len(vistos)} eventos vistos.")


if __name__ == "__main__":
    main()
