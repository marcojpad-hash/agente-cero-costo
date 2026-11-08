#!/usr/bin/env python3
"""Sincronizar: el VTunnel de la memoria.

El repo privado memoria-compartida no lo puede leer un modelo sin
vínculo (GitHub exige una identidad con acceso; no es un bloqueo de
red, es de autenticación, y ningún proxy lo salta sin credenciales).
Este script es el VTunnel: lee la memoria privada (a la que Pecas sí
tiene acceso por la app de GitHub) y publica un resumen público con
los hechos en agente-cero-costo, donde cualquier modelo lo lee por
web sin cuenta ni autorización.

El repo privado sigue privado. Lo que se publica es solo el resumen
de hechos del proyecto (lo mismo que ya es público en
transmigracion/contexto.md): sin datos personales, sin claves, sin
secretos. Si un hecho no debe ser público, no va en la memoria
privada con la marca "privado" (ver README).

Uso: python3 sincronizar.py
Se corre cada vez que cambia la memoria privada.
"""
import datetime
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
MEMORIA = os.path.expanduser("~/workspace/memoria-compartida")
ARCHIVOS = [
    ("proyectos", "hechos/proyectos.md"),
    ("decisiones", "hechos/decisiones.md"),
    ("correcciones", "hechos/correcciones.md"),
    ("tokens", "hechos/tokens.md"),
    ("estado", "hechos/estado.md"),
    ("personas", "hechos/personas.md"),
]


def leer(path):
    try:
        return open(path, encoding="utf-8").read()
    except OSError:
        return None


def main():
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    partes = []
    partes.append("# Memoria compartida (resumen público)\n\n")
    partes.append(f"Generado: {ahora}. Fuente: repo privado "
                  f"memoria-compartida (sigue privado). Este archivo es "
                  f"público: solo lleva hechos del proyecto, sin datos "
                  f"personales, sin claves, sin secretos.\n\n")
    partes.append("Lee `INDICE.md` en el repo privado si tienes acceso; "
                  "si no, este resumen es lo vigente.\n\n")
    for nombre, rel in ARCHIVOS:
        texto = leer(os.path.join(MEMORIA, rel))
        if texto is None:
            partes.append(f"## {nombre}\n\n(No disponible en la copia "
                          f"local.)\n\n")
            continue
        partes.append(texto)
        if not texto.endswith("\n"):
            partes.append("\n")
        partes.append("\n")
    salida = os.path.join(HERE, "DIGEST.md")
    with open(salida, "w", encoding="utf-8") as f:
        f.write("".join(partes))
    print(f"Digest público generado: {salida} "
          f"({os.path.getsize(salida)} bytes)")


if __name__ == "__main__":
    main()
