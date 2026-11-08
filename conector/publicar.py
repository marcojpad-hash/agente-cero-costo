#!/usr/bin/env python3
"""Publicar: el foquito.

Genera el estado vigente en dos formas que cualquier modelo puede leer
por web, sin scripts ni repo:
- conector/ESTADO.md (legible, para personas y modelos)
- conector/estado.json (para máquinas)

La dirección pública es la URL cruda de GitHub, que ya existe sin
configurar nada:
  https://raw.githubusercontent.com/marcojpad-hash/agente-cero-costo/main/conector/ESTADO.md
  https://raw.githubusercontent.com/marcojpad-hash/agente-cero-costo/main/conector/estado.json

Ese es el lado receptor para los modelos que viven en su propia app
(ChatGPT, Grok, Gemini): no tienen el repo ni los scripts, pero todos
navegan. Leen esa URL antes de responder y ya tienen los datos
actualizados. El lado emisor es el bloque [EMITIR] (ver
conector/emitir-bloque.md) que el modelo produce y el usuario pega
aquí; aplicar.py lo escribe en el bus.

Uso: python3 publicar.py
Se corre solo cada vez que hay una actualización (avisar.py y emitir.py
ya lo llaman).
"""
import datetime
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BASE_RAW = ("https://raw.githubusercontent.com/marcojpad-hash/"
            "agente-cero-costo/main/conector")


def leer(path):
    try:
        return open(path, encoding="utf-8").read()
    except OSError:
        return ""


def main():
    version = leer(os.path.join(REPO, "avisos", "VERSION")).strip() or "0"
    log = leer(os.path.join(REPO, "avisos", "ACTUALIZACIONES.md"))
    lineas = [l for l in log.splitlines() if l.startswith("- ")]
    ultima = lineas[-1][2:] if lineas else "Sin actualizaciones."
    bus = os.path.join(HERE, "bus")
    n_bus = len([n for n in os.listdir(bus) if n.endswith(".json")]) \
        if os.path.isdir(bus) else 0
    tablero = leer(os.path.expanduser(
        "~/workspace/cbm-repos/capcot-capsulas-imaginantes/"
        "ajustes_entre_modelos/DELEGACIONES.md"))
    pendientes = tablero.count("ESTADO: PENDIENTE") if tablero else 0
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    estado = {
        "version": int(version) if version.isdigit() else version,
        "fecha": ahora,
        "ultima_actualizacion": ultima,
        "pendientes_tablero_capcot": pendientes,
        "eventos_bus": n_bus,
        "estado_md": f"{BASE_RAW}/ESTADO.md",
        "como_emitir": f"{BASE_RAW}/emitir-bloque.md",
    }
    with open(os.path.join(HERE, "estado.json"), "w",
              encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)
    md = []
    md.append("# Estado vigente del stack\n\n")
    md.append(f"Versión: {version} — Fecha: {ahora}\n\n")
    md.append(f"Última actualización: {ultima}\n\n")
    md.append(f"Pendientes en el tablero CAPCOT: {pendientes}\n\n")
    md.append(f"Eventos en el bus: {n_bus}\n\n")
    md.append("## Para el modelo que lee esto\n\n")
    md.append("Usa esta versión y esta última actualización como el estado "
              "vigente. Si tienes información nueva para el equipo, "
              "emítela con el bloque [EMITIR] (ver emitir-bloque.md en "
              "este mismo directorio) y el usuario la pegará en el "
              "sistema.\n")
    with open(os.path.join(HERE, "ESTADO.md"), "w", encoding="utf-8") as f:
        f.write("".join(md))
    print(f"Publicado: ESTADO.md y estado.json (v{version})")
    print(f"URL pública: {BASE_RAW}/ESTADO.md")


if __name__ == "__main__":
    main()
