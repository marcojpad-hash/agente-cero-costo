#!/usr/bin/env python3
"""Recibir: el enchufe hembra del conector.

Lee el bus compartido (conector/bus/) y entrega solo los eventos
nuevos desde la última lectura, usando un watermark local (qué ya vio
este receptor). Después de entregarlos, guarda el watermark nuevo.
Con --solo-ver no lo guarda: solo mira qué hay nuevo.

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


def cargar_visto(ruta):
    try:
        return json.load(open(ruta, encoding="utf-8")).get("ultimo_id", "")
    except (OSError, ValueError, AttributeError):
        return ""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--visto", default=VISTO_DEF)
    parser.add_argument("--solo-ver", action="store_true")
    args = parser.parse_args()
    ultimo = cargar_visto(args.visto)
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
            if ev.get("id", "") > ultimo:
                eventos.append(ev)
    if not eventos:
        print("Sin novedades: no hay eventos nuevos en el bus.")
        return
    print(f"Eventos nuevos: {len(eventos)}")
    for ev in eventos:
        print(f"- {ev.get('fecha')} (v{ev.get('version')}, "
              f"{ev.get('tipo')}, de {ev.get('de')}): {ev.get('mensaje')}")
    if not args.solo_ver:
        os.makedirs(os.path.dirname(args.visto), exist_ok=True)
        with open(args.visto, "w", encoding="utf-8") as f:
            json.dump({"ultimo_id": eventos[-1]["id"]}, f)
        print(f"Watermark guardado: {eventos[-1]['id']}")


if __name__ == "__main__":
    main()
