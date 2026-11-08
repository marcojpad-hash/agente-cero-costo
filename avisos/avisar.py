#!/usr/bin/env python3
"""Avisos: el callback de actualización.

Cada vez que se da una indicación o cambia la información, se avisa:
los otros modelos, aunque no estén en la interacción directa, reciben
la indicación de que hay actualización. Así, si el usuario cambia de
aplicación, el modelo que le toque ya tiene los datos actualizados.

Cómo funciona (patrón verificado por búsqueda 2026-11-08: Hermes Agent
usa un watermark y polling; Composio inyecta el issue en el prompt del
agente; IssueClaw y harnext usan Issues + Actions):
1. Se escribe la actualización en ACTUALIZACIONES.md (registro
   cronológico, solo se agrega, nunca se borra).
2. Se sube VERSION (el watermark): cualquier modelo compara su copia
   con este número y sabe si está desactualizado.
3. Se regenera ULTIMA_ACTUALIZACION.md (la nota corta que se adjunta
   a cada encargo) y el paquete de transmigración (empaquetar.py).
4. Los canales que leen el repo (orquestador diario, relevo cada hora)
   ven la actualización en su siguiente corrida. El issue de GitHub
   (workflow avisos.yml, por navegador) la publica para Copilot.

Los modelos de API (Gemini, Groq) no tienen buzón: su aviso es el
contexto que la sanguijuela adjunta automáticamente a cada encargo
(versión + últimas actualizaciones).

Uso: python3 avisar.py "mensaje de la actualización"
"""
import datetime
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
VERSION_F = os.path.join(HERE, "VERSION")
LOG_F = os.path.join(HERE, "ACTUALIZACIONES.md")
ULTIMA_F = os.path.join(HERE, "ULTIMA_ACTUALIZACION.md")
EMPAQUETAR = os.path.join(REPO, "transmigracion", "empaquetar.py")
PUBLICAR = os.path.join(REPO, "conector", "publicar.py")


def leer_version():
    try:
        return int(open(VERSION_F, encoding="utf-8").read().strip())
    except (OSError, ValueError):
        return 0


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 avisar.py \"mensaje de la actualización\"")
        sys.exit(1)
    mensaje = sys.argv[1].strip()
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    version = leer_version() + 1
    with open(VERSION_F, "w", encoding="utf-8") as f:
        f.write(f"{version}\n")
    with open(LOG_F, "a", encoding="utf-8") as f:
        f.write(f"- {ahora} (v{version}) — {mensaje}\n")
    with open(ULTIMA_F, "w", encoding="utf-8") as f:
        f.write(f"# Última actualización\n\nVersión: {version}\n\n"
                f"Fecha: {ahora}\n\n{mensaje}\n\n"
                f"Registro completo: ACTUALIZACIONES.md\n")
    r = subprocess.run([sys.executable, EMPAQUETAR],
                       capture_output=True, text=True)
    p = subprocess.run([sys.executable, PUBLICAR],
                       capture_output=True, text=True)
    print(f"Aviso v{version} registrado: {mensaje}")
    print(f"Canales: registro en el repo, VERSION={version}, "
          f"transmigración regenerada ({r.stdout.strip().splitlines()[0] if r.stdout else 'sin salida'}), "
          f"estado público regenerado ({p.stdout.strip().splitlines()[0] if p.stdout else 'sin salida'}).")
    print("Lo verán en su siguiente corrida: orquestador diario, relevo "
          "cada hora, y la sanguijuela lo adjunta a cada encargo.")


if __name__ == "__main__":
    main()
