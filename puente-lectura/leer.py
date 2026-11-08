#!/usr/bin/env python3
"""Puente de lectura: cuando Pecas no puede leer algo, lo leen los otros
modelos y lo unifican.

La idea es de Marco: los modelos que tenemos son otras arquitecturas de
otras compañías, con capacidades diferentes. Si uno no puede leer un
texto (por ejemplo un README que no se abre por timeout), otro sí puede,
y entre ellos lo unifican.

Cómo funciona:
1. Trae el texto por varias rutas: raw.githubusercontent.com para
   archivos de GitHub, la API de GitHub (get_file_contents) como
   respaldo, y lectura directa con User-Agent de navegador para el resto.
   Si ninguna ruta trae el texto, lo dice y no inventa nada.
2. Le pasa el texto a Gemini (gemini-3-flash-preview) y a Groq
   (openai/gpt-oss-20b) para que cada uno extraiga lo mismo: qué
   problema resuelve, cómo funciona, qué cuesta, qué se puede copiar y
   los límites honestos.
3. Le pide a Gemini que una las dos lecturas en una sola nota, sin
   repetir, marcando donde discrepen. Si un modelo falla, la nota usa
   al otro y dice cuál falló y por qué.

Las claves nunca pasan por este archivo: los clientes de los conectores
las resuelven solos. El texto se trunca a 12.000 caracteres para que
quepa en el minuto gratis de Groq (8.000 TPM); la nota dice si hubo
truncamiento.

Uso:
    python3 leer.py <URL> [<URL> ...] [--salida ARCHIVO]
"""
import argparse
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

GEMINI_CLIENT = "/home/hatch/workspace/custom-connectors/custom.gemini/bin/client.py"
GROQ_CLIENT = "/home/hatch/workspace/custom-connectors/custom.groq/bin/client.py"
GITHUB_CLI = "/opt/hatch/bin/github"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
MAX_CHARS = 12000

EXTRAER = """Lee este texto (es un README o documento de un repositorio de GitHub) y extrae, en español, en forma de lista corta:
- Qué problema resuelve
- Cómo funciona (el mecanismo concreto)
- Qué cuesta
- Qué se puede copiar o adaptar para un stack de agente a costo cero
- Límites honestos (qué no hace o dónde falla)
Si el texto está truncado, di solo lo que el texto trae, sin inventar nada.

TEXTO:
"""

UNIR = """Une estas dos lecturas del mismo texto en una sola nota, en español, sin repetir información. Si discrepan en algo, marca la discrepancia y di cuál lectura dice qué. Si una lectura dice que algo no se pudo leer, consérvalo como advertencia.

LECTURA 1 (Gemini):
{uno}

LECTURA 2 (Groq):
{dos}

NOTA UNIFICADA:
"""


def fetch_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_github(url):
    """Para github.com/<owner>/<repo>/blob/<branch>/<path>: intenta el
    raw y, si falla, la API de GitHub (get_file_contents)."""
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)", url)
    if m:
        owner, repo, branch, path = m.groups()
        if branch != "HEAD":
            try:
                return fetch_url(
                    f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"
                ), "raw.githubusercontent.com"
            except Exception:
                pass
        try:
            r = subprocess.run(
                [GITHUB_CLI, "call-read-tool", "--name", "get_file_contents",
                 "--arguments-json", json.dumps(
                     {"owner": owner, "repo": repo, "path": path})],
                capture_output=True, text=True, timeout=120,
            )
            data = json.loads(r.stdout)
            for item in data.get("result", {}).get("content", []):
                res = item.get("resource")
                if res and res.get("text"):
                    return res["text"], "API de GitHub (get_file_contents)"
        except Exception:
            pass
        raise RuntimeError("ninguna ruta de GitHub trajo el archivo")
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/?$", url)
    if m:
        owner, repo = m.groups()
        try:
            r = subprocess.run(
                [GITHUB_CLI, "call-read-tool", "--name", "get_file_contents",
                 "--arguments-json", json.dumps(
                     {"owner": owner, "repo": repo, "path": "README.md"})],
                capture_output=True, text=True, timeout=120,
            )
            data = json.loads(r.stdout)
            for item in data.get("result", {}).get("content", []):
                res = item.get("resource")
                if res and res.get("text"):
                    return res["text"], "API de GitHub (get_file_contents)"
        except Exception:
            pass
        raise RuntimeError("ninguna ruta de GitHub trajo el README")
    return fetch_url(url), "lectura directa"


def llamar(cliente, args, prompt):
    r = subprocess.run(
        [sys.executable, cliente] + args + ["--prompt", prompt],
        capture_output=True, text=True, timeout=300,
    )
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip()[:300])
    return r.stdout.strip()


def leer_url(url, contexto=None):
    print(f"\n## {url}", flush=True)
    try:
        texto, ruta = fetch_github(url)
    except Exception as exc:
        print(f"NO SE PUDO LEER: {exc}", flush=True)
        return f"## {url}\n\nNo se pudo leer por ninguna ruta ({exc}). No se inventó nada.\n"
    truncado = len(texto) > MAX_CHARS
    if truncado:
        texto = texto[:MAX_CHARS]
    print(f"Texto traído por {ruta} ({len(texto)} caracteres"
          + (", truncado" if truncado else "") + ")", flush=True)
    extraer = (contexto + "\n\n" if contexto else "") + EXTRAER + texto
    extracciones = {}
    try:
        extracciones["Gemini"] = llamar(
            GEMINI_CLIENT,
            ["generate", "--model", "gemini-3-flash-preview"],
            extraer,
        )
        print("Gemini leyó.", flush=True)
    except Exception as exc:
        extracciones["Gemini"] = None
        print(f"Gemini falló: {exc}", flush=True)
    time.sleep(15)
    try:
        extracciones["Groq"] = llamar(
            GROQ_CLIENT,
            ["chat", "--model", "openai/gpt-oss-20b"],
            extraer,
        )
        print("Groq leyó.", flush=True)
    except Exception as exc:
        extracciones["Groq"] = None
        print(f"Groq falló: {exc}", flush=True)
    nota = f"## {url}\n\nRuta: {ruta}. Truncado: {'sí' if truncado else 'no'}.\n\n"
    if extracciones.get("Gemini") and extracciones.get("Groq"):
        time.sleep(15)
        try:
            unificada = llamar(
                GEMINI_CLIENT,
                ["generate", "--model", "gemini-3-flash-preview"],
                UNIR.format(uno=extracciones["Gemini"], dos=extracciones["Groq"]),
            )
            nota += "### Nota unificada (Gemini + Groq)\n\n" + unificada + "\n"
        except Exception as exc:
            nota += (f"### No se pudo unificar ({exc})\n\n"
                     f"#### Gemini\n\n{extracciones['Gemini']}\n\n"
                     f"#### Groq\n\n{extracciones['Groq']}\n")
    elif extracciones.get("Gemini"):
        nota += "### Nota (solo Gemini; Groq falló)\n\n" + extracciones["Gemini"] + "\n"
    elif extracciones.get("Groq"):
        nota += "### Nota (solo Groq; Gemini falló)\n\n" + extracciones["Groq"] + "\n"
    else:
        nota += "Ningún modelo pudo leer el texto.\n"
    print(nota, flush=True)
    return nota


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+")
    parser.add_argument("--salida", default=None)
    parser.add_argument("--contexto", default=None,
                        help="Contexto vigente que se antepone a la lectura")
    args = parser.parse_args()
    notas = []
    for url in args.urls:
        notas.append(leer_url(url, args.contexto))
    salida = "# Lecturas por el puente\n\n" + "\n".join(notas)
    if args.salida:
        open(args.salida, "w", encoding="utf-8").write(salida)
        print(f"\nGuardado en: {args.salida}", flush=True)


if __name__ == "__main__":
    main()
