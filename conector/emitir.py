#!/usr/bin/env python3
"""Emitir: el enchufe (macho) del conector.

Escribe un evento en el bus compartido (conector/bus/) y avisa por el
callback (avisos/avisar.py) para que la versión suba. El receptor
(recibir.py) es el otro lado del conector: lee el bus y entrega solo
los eventos nuevos. Los dos lados encajan porque hablan el mismo
formato (el pinout, ver conector/README.md).

El par es reversible: cualquier modelo puede emitir y cualquier modelo
puede recibir. El que emite hoy puede recibir mañana, y viceversa.

El bus es el repo: los eventos viajan con GitHub, así que cualquier
modelo que tenga el repo los ve. El watermark (qué ya vio cada
receptor) es local de cada máquina, nunca va en el repo.

Uso:
    python3 emitir.py "mensaje" [--tipo actualizacion|indicacion|aviso|hecho] [--de NOMBRE]
"""
import argparse
import datetime
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BUS = os.path.join(HERE, "bus")
AVISAR = os.path.join(REPO, "avisos", "avisar.py")
FORMATO = 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mensaje")
    parser.add_argument("--tipo", default="actualizacion",
                        choices=["actualizacion", "indicacion", "aviso", "hecho"])
    parser.add_argument("--de", default="Pecas")
    args = parser.parse_args()
    os.makedirs(BUS, exist_ok=True)
    ahora = datetime.datetime.now()
    eid = ahora.strftime("%Y%m%d-%H%M%S-%f")
    fecha = ahora.strftime("%Y-%m-%d %H:%M")
    # La versión sube con el aviso; se lee después de avisar.
    subprocess.run([sys.executable, AVISAR, args.mensaje],
                   check=True, capture_output=True, text=True)
    try:
        version = int(open(os.path.join(REPO, "avisos", "VERSION"),
                           encoding="utf-8").read().strip())
    except (OSError, ValueError):
        version = 0
    evento = {
        "formato": FORMATO,
        "id": eid,
        "fecha": fecha,
        "version": version,
        "de": args.de,
        "tipo": args.tipo,
        "mensaje": args.mensaje,
    }
    ruta = os.path.join(BUS, f"{eid}.json")
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(evento, f, ensure_ascii=False, indent=2)
    print(f"Emitido: {eid} (v{version}, {args.tipo}, de {args.de})")
    print(f"Evento: conector/bus/{eid}.json")
    print("El receptor lo verá en su siguiente lectura.")


if __name__ == "__main__":
    main()
