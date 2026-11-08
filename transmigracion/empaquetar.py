#!/usr/bin/env python3
"""Empaqueta la transmigración: regenera MANIFIESTO.md y contexto.md
desde las fuentes vivas.

El paquete es la clonación de capacidades: el método, las herramientas
(código real) y el estado (qué está pendiente, qué se decidió, qué se
aprendió). No es un prompt que imita un personaje.

Fuentes:
- El tablero: copia local de CAPCOT
  (~/workspace/cbm-repos/capcot-capsulas-imaginantes/ajustes_entre_modelos/DELEGACIONES.md).
  Si la copia es vieja, el estado es viejo: hacer git pull antes.
- La skill de cómo trabajar con Marco
  (~/workspace/custom-skills/trabajar-con-marco/SKILL.md): solo se
  registra su fecha, el método vive en metodo.md.
- El árbol de este repo: inventario de herramientas reales.

No lleva claves, contraseñas ni datos personales. Nada de eso va en
ningún repo, ni privado.

Uso: python3 empaquetar.py
"""
import datetime
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SKILL = os.path.expanduser(
    "~/workspace/custom-skills/trabajar-con-marco/SKILL.md")
TABLERO = os.path.expanduser(
    "~/workspace/cbm-repos/capcot-capsulas-imaginantes/"
    "ajustes_entre_modelos/DELEGACIONES.md")
VERSION = "0.1"


def fecha_archivo(path):
    if not os.path.exists(path):
        return None
    ts = os.path.getmtime(path)
    return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def leer(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def arbol():
    out = subprocess.run(
        ["find", ".", "-type", "f", "-not", "-path", "./.git/*"],
        cwd=REPO, capture_output=True, text=True)
    return sorted(out.stdout.splitlines())


def contexto():
    hoy = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    tablero = leer(TABLERO)
    f_tablero = fecha_archivo(TABLERO)
    f_skill = fecha_archivo(SKILL)
    lineas = []
    lineas.append("# Contexto\n")
    lineas.append(f"Foto del estado tomada el {hoy} por empaquetar.py.\n")
    lineas.append("## Quiénes somos\n")
    lineas.append("- **Marco Antonio Juárez (Marco)**: solo celular Android, "
                 "sin computadora. Depende del agente para GitHub, subidas "
                 "y YouTube Studio. Dicta por voz: las palabras salen "
                 "deformadas; interpretar por contexto.\n")
    lineas.append("- **Pecas**: el agente. Coordina, prepara borradores y "
                 "paquetes, verifica. No monta el MP4 final ni publica.\n")
    lineas.append("## Proyectos\n")
    lineas.append("- **CAPCOT** (marcojpad-hash/capcot-capsulas-imaginantes, "
                 "público): cápsulas científicas verticales 9:16 de 60-90 s, "
                 "serie «Datos y ociosidades», en español es-MX. Imaginantes "
                 "monta el MP4 oficial con voz es-MX-JorgeNeural, corre QA "
                 "y programa.\n")
    lineas.append("- **Motor U6** (marcojpad-hash/motor-u6-storage, privado): "
                 "proyecto aparte, no parte de CAPCOT. Engine V5 canónico y "
                 "catálogo 244 son la referencia fija.\n")
    lineas.append("- **agente-cero-costo** (este repo, público): stack de "
                 "agente a costo cero — puente Groq, dsh, orquestador, "
                 "puente de lectura, máquina en el repo, transmigración.\n")
    lineas.append("- **baterias-tokens** (privado): proveedores gratuitos, "
                 "rotación, puente Groq, protocolo de relevo.\n")
    lineas.append("- **baterias-memoria** (privado): máquinas, modelos y "
                 "memoria.\n")
    lineas.append("- **ChatGPT-migracion** (privado): bandeja entre modelos.\n")
    lineas.append("- **orquestador-central** (público): contrato transversal "
                 "multi-modelo; lo está armando alguien más. No confundir "
                 "con el orquestador de este repo.\n")
    lineas.append("## Tablero (delegaciones pendientes)\n")
    if tablero:
        lineas.append(f"Fuente: copia local de CAPCOT, archivo del "
                      f"{f_tablero}. Si la copia es vieja, hacer git pull "
                      "y regenerar.\n\n")
        lineas.append(tablero)
    else:
        lineas.append("El tablero no estaba disponible en la copia local. "
                      "No se inventó nada: leerlo en el repo CAPCOT, "
                      "ajustes_entre_modelos/DELEGACIONES.md.\n")
    lineas.append("\n## Decisiones y correcciones\n")
    lineas.append("- El motor U6 y CAPCOT son dos proyectos diferentes. El "
                 "callback no va en el motor.\n")
    lineas.append("- El montaje oficial, QA y programación son de "
                 "Imaginantes. Pecas no monta MP4 final ni publica.\n")
    lineas.append("- Todo el contenido CAPCOT en español es-MX.\n")
    lineas.append("- No inventar datos, fuentes ni DOIs.\n")
    lineas.append("- La app de GitHub no tiene permiso Workflows: los "
                 "workflows van por navegador con la cuenta de Marco. "
                 "La app sí puede crear repos por API si tiene el permiso "
                 "Repository creation.\n")
    lineas.append("- Las claves guardadas no se pueden leer de vuelta: se "
                 "usan por conector, nunca se pegan en un repo.\n")
    lineas.append("- El relevo: cuando el agente se queda sin tokens, "
                 "gpt-oss-120b toma el tablero en Actions cada hora.\n")
    lineas.append("## Tokens (foto)\n")
    lineas.append("- Muse gratis: 100% usado al 2026-11-07, reinicio "
                 "2026-11-13 a las 17:24 CST. Fondo aparte de tokens "
                 "adicionales: 2% usado, 983M restantes. La generación de "
                 "video es el principal costo; el texto va con Gemini/Groq.\n")
    lineas.append("- Groq gratis: 8.000 TPM. El prompt de dsh pesa ~4.600 "
                 "tokens: la segunda llamada da 429.\n")
    lineas.append("- Gemini gratis: 1M TPM (según IssueClaw). Es el primario "
                 "para tareas largas.\n")
    lineas.append(f"\nSkill de cómo trabajar con Marco: archivo del "
                  f"{f_skill or 'no disponible'}.\n")
    lineas.append("\nEste paquete no lleva claves, contraseñas ni datos "
                 "personales.\n")
    return "".join(lineas)


def manifiesto(files):
    hoy = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    lineas = []
    lineas.append("# Manifiesto de transmigración\n\n")
    lineas.append(f"Versión: {VERSION}\n\n")
    lineas.append(f"Generado: {hoy}\n\n")
    lineas.append("Este paquete clona **capacidades, no el personaje**. "
                 "Cualquier modelo, en cualquier sesión, de cualquier "
                 "empresa, puede cargarlo y tener la misma información.\n\n")
    lineas.append("## Contenido del paquete\n\n")
    for f in ["README.md", "metodo.md", "capacidades.md", "contexto.md",
              "arranque.md", "MANIFIESTO.md", "empaquetar.py"]:
        lineas.append(f"- transmigracion/{f}\n")
    lineas.append("\n## Herramientas del repo (inventario)\n\n")
    for f in files:
        if f.startswith("./transmigracion/"):
            continue
        lineas.append(f"- {f}\n")
    lineas.append("\n## Fuentes\n\n")
    lineas.append(f"- Tablero: copia local de CAPCOT, archivo del "
                  f"{fecha_archivo(TABLERO) or 'no disponible'}.\n")
    lineas.append(f"- Skill: {fecha_archivo(SKILL) or 'no disponible'}.\n")
    lineas.append("- Estado de tokens: foto del 2026-11-07, revisar.\n")
    return "".join(lineas)


def main():
    files = arbol()
    with open(os.path.join(HERE, "contexto.md"), "w",
              encoding="utf-8") as f:
        f.write(contexto())
    with open(os.path.join(HERE, "MANIFIESTO.md"), "w",
              encoding="utf-8") as f:
        f.write(manifiesto(files))
    print(f"Paquete v{VERSION} generado: contexto.md y MANIFIESTO.md")
    print(f"Archivos en el repo: {len(files)}")


if __name__ == "__main__":
    main()
