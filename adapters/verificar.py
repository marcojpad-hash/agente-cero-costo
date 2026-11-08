#!/usr/bin/env python3
"""Prueba: que ningún adaptador pierda instrucciones.

Lee la definición canónica y los tres archivos generados
(claude.md, codex.toml, gemini.md) y comprueba que las frases
clave del contrato (identidad, procedimiento y criterios de éxito)
estén presentes en los tres. Si una frase falta en un formato, la
conversión perdió una instrucción y la prueba falla.

No comprueba la validez del esquema TOML de Codex; eso se verifica
contra Codex antes de usarlo en producción.

Uso: python3 verificar.py
Sale con código 0 si todo pasa, 1 si algo falta.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BASE = os.path.join(REPO, "agents", "sequential-verifiable")
SALIDA = os.path.join(HERE, "salida")

# Frases clave del contrato. Tienen que estar en los tres formatos.
FRASES = [
    "ejecuta un contrato de trabajo paso a paso",
    "resultado verificable en cada paso",
    "No inventar datos, fuentes ni resultados",
    "Leer el encargo completo antes de actuar",
    "Sin evidencia, el paso no cuenta",
    "Sin datos inventados",
    "Resultado en su lugar",
    "Pendientes declarados",
    "Sin secretos expuestos",
    "No monta el MP4 oficial",
    "No guarda claves, contraseñas ni datos personales",
]


def leer(ruta):
    with open(ruta, encoding="utf-8") as f:
        return f.read()


def main():
    formatos = {
        "claude.md": os.path.join(SALIDA, "claude.md"),
        "codex.toml": os.path.join(SALIDA, "codex.toml"),
        "gemini.md": os.path.join(SALIDA, "gemini.md"),
    }
    fallos = 0
    for nombre, ruta in formatos.items():
        if not os.path.exists(ruta):
            print(f"FAIL {nombre}: no existe (corre generar.py)")
            fallos += 1
            continue
        texto = leer(ruta)
        faltan = [f for f in FRASES if f not in texto]
        if faltan:
            fallos += len(faltan)
            print(f"FAIL {nombre}: faltan {len(faltan)} frases:")
            for f in faltan:
                print(f"  - {f}")
        else:
            print(f"OK {nombre}: {len(FRASES)}/{len(FRASES)} frases")
    if fallos:
        print(f"\nPrueba FALLIDA: {fallos} problemas")
        sys.exit(1)
    print("\nPrueba OK: las tres salidas conservan el contrato")
    sys.exit(0)


if __name__ == "__main__":
    main()
