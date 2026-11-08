#!/usr/bin/env python3
"""Aplicar: escribe en el bus un bloque [EMITIR] pegado.

El modelo que vive en su propia app no puede escribir en el repo, pero
puede emitir el bloque (ver conector/emitir-bloque.md). El usuario pega
la respuesta del modelo aquí y este script la aplica: valida el bloque,
escribe el evento en el bus y avisa por el callback.

Uso:
    python3 aplicar.py <archivo-con-el-bloque>
    cat bloque.txt | python3 aplicar.py
"""
import json
import os
import re
import subprocess
import sys
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BUS = os.path.join(HERE, "bus")
AVISAR = os.path.join(REPO, "avisos", "avisar.py")
TIPOS = ["actualizacion", "indicacion", "aviso", "hecho"]


def main():
    if len(sys.argv) > 1:
        texto = open(sys.argv[1], encoding="utf-8").read()
    else:
        texto = sys.stdin.read()
    m = re.search(r"\[EMITIR\](.*?)\[/EMITIR\]", texto, re.S)
    if not m:
        print("No se encontró ningún bloque [EMITIR]...[/EMITIR].")
        sys.exit(1)
    campos = {}
    for linea in m.group(1).strip().splitlines():
        if ":" in linea:
            k, v = linea.split(":", 1)
            campos[k.strip().lower()] = v.strip()
    de = campos.get("de", "")
    tipo = campos.get("tipo", "")
    mensaje = campos.get("mensaje", "")
    if not de or tipo not in TIPOS or not mensaje:
        print("Bloque inválido: necesita de, tipo "
              f"({', '.join(TIPOS)}) y mensaje.")
        sys.exit(1)
    os.makedirs(BUS, exist_ok=True)
    ahora = datetime.datetime.now()
    eid = ahora.strftime("%Y%m%d-%H%M%S-%f")
    subprocess.run([sys.executable, AVISAR, mensaje],
                   check=True, capture_output=True, text=True)
    try:
        version = int(open(os.path.join(REPO, "avisos", "VERSION"),
                           encoding="utf-8").read().strip())
    except (OSError, ValueError):
        version = 0
    evento = {
        "formato": 1,
        "id": eid,
        "fecha": ahora.strftime("%Y-%m-%d %H:%M"),
        "version": version,
        "de": de,
        "tipo": tipo,
        "mensaje": mensaje,
    }
    with open(os.path.join(BUS, f"{eid}.json"), "w",
              encoding="utf-8") as f:
        json.dump(evento, f, ensure_ascii=False, indent=2)
    print(f"Aplicado: {eid} (v{version}, {tipo}, de {de})")
    print(f"Evento: conector/bus/{eid}.json")


if __name__ == "__main__":
    main()
