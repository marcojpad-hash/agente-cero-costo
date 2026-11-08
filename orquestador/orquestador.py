#!/usr/bin/env python3
"""Orquestador de CAPCOT.

El coordinador que no se muere: un modelo abierto (gpt-oss-120b, Apache 2.0)
por la API gratuita de Groq, con el cableado para leer el tablero de
delegaciones y decir qué está atorado, quién debe qué a quién y cuál es el
siguiente paso de cada pendiente.

Uso:
    python3 orquestador.py [--repo RUTA] [--salida RUTA] [--model MODELO]
                           [--api-key-env NOMBRE]

- --repo: clon local de capcot-capsulas-imaginantes (por defecto el espejo
  de Pecas). El script hace git pull si puede; si no, usa la copia local
  y lo dice en el reporte.
- --salida: dónde escribir el reporte (por defecto ./reporte.md).
- --model: modelo de Groq (por defecto openai/gpt-oss-120b).
- --api-key-env: nombre de la variable de entorno con la clave de Groq.
  Solo para correr fuera de la máquina de Pecas (por ejemplo en GitHub
  Actions, con la clave en un secreto del repo). En la máquina de Pecas
  no se usa: ahí va por el conector.

No gasta tokens de Muse y no tiene saldo que se agote: la API de Groq es
gratuita y el orquestador corre unas pocas veces al día. Copilot ya no es
el orquestador: su uso libre es limitado y se murió en ese papel.
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

GROQ_CLIENT = Path.home() / "workspace/custom-connectors/custom.groq/bin/client.py"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b"

REGLAS = """Reglas que no se te pueden olvidar:
- Imaginantes monta el MP4 oficial con la voz es-MX-JorgeNeural y corre el QA oficial. Si está pausado por ahorro de créditos, la cápsula espera: no se reasigna a otro modelo.
- Pecas NO puede subir archivos de .github/workflows/ por API (la app de Muse no tiene permiso Workflows). Esos archivos los sube Marco por navegador.
- Marco es quien crea las cuentas (por ejemplo Clayzo) y quien activa cosas en Settings de GitHub. Pecas no tiene sus contraseñas.
- Copilot trabaja en el repo, pero ya NO es el orquestador.
- No inventes datos, fuentes ni DOIs. Si algo no está en el tablero, di que no está."""


def leer(ruta):
    return Path(ruta).read_text(encoding="utf-8")


def llamar_groq(prompt, model, api_key_env=None):
    """Llama a Groq y devuelve el texto. Sin api_key_env usa el conector
    de Pecas; con api_key_env lee la clave de esa variable de entorno
    (para GitHub Actions) y llama directo a la API."""
    if api_key_env:
        key = os.environ.get(api_key_env)
        if not key:
            raise SystemExit(f"falta la variable {api_key_env} con la clave de Groq")
        body = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8")
        req = urllib.request.Request(
            GROQ_URL, data=body,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.load(resp)
        return data["choices"][0]["message"]["content"]
    r = subprocess.run(
        [sys.executable, str(GROQ_CLIENT), "chat", "--model", model, "--prompt", prompt],
        capture_output=True, text=True, timeout=300,
    )
    if r.returncode != 0:
        print(f"El modelo no respondió:\n{r.stderr}", file=sys.stderr)
        raise SystemExit(1)
    return r.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=str(Path.home() / "workspace/cbm-repos/capcot-capsulas-imaginantes"))
    parser.add_argument("--salida", default="reporte.md")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--api-key-env", default=None)
    args = parser.parse_args()

    repo = Path(args.repo)
    pull = subprocess.run(
        ["git", "-C", str(repo), "pull", "--ff-only", "-q"],
        capture_output=True, text=True,
    )
    if pull.returncode == 0:
        aviso_pull = "Tablero actualizado con git pull."
    else:
        aviso_pull = "No se pudo hacer git pull; se usó la copia local del tablero."
    tablero = leer(repo / "ajustes_entre_modelos/DELEGACIONES.md")
    protocolo = leer(repo / "ajustes_entre_modelos/PROTOCOLO_CALLBACK.md")

    prompt = (
        "Eres el coordinador del proyecto CAPCOT (cápsulas científicas verticales en español es-MX).\n"
        "Tu trabajo es leer el tablero de delegaciones y el protocolo, y decir qué está atorado, "
        "quién debe qué a quién y cuál es el siguiente paso concreto de cada pendiente.\n\n"
        f"{REGLAS}\n\n"
        "PROTOCOLO:\n" + protocolo + "\n\n"
        "TABLERO:\n" + tablero + "\n\n"
        "Responde en español, en forma de lista, un renglón por pendiente: qué está atorado, "
        "quién debe qué a quién y el siguiente paso concreto. Sin relleno."
    )

    texto = llamar_groq(prompt, args.model, args.api_key_env)

    ahora = datetime.now().strftime("%Y-%m-%d %H:%M")
    reporte = (
        f"# Reporte del orquestador — {ahora}\n"
        f"Modelo: {args.model} (Groq, API gratuita)\n"
        f"{aviso_pull}\n\n"
        + texto + "\n"
    )
    Path(args.salida).write_text(reporte, encoding="utf-8")
    print(reporte)
    print(f"\nGuardado en: {args.salida}")


if __name__ == "__main__":
    main()
