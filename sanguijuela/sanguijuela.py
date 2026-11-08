#!/usr/bin/env python3
"""Sanguijuela: el que orquesta no gasta sus tokens.

Recibe un encargo, lo enruta al modelo gratuito que corresponde según
el protocolo (PROTOCOLO_SANGUIJUELA.md) y trae el resultado. El
orquestador solo escribe el encargo corto; el trabajo pesado lo hace
el modelo gratuito, con sus tokens.

Tipos:
- texto: razonamiento, plan, resumen corto -> Groq gpt-oss-20b
- texto-largo: contexto grande, código largo -> Gemini gemini-3-flash-preview
- lectura: una URL que no se abre -> puente-lectura (Gemini + Groq)
- codigo: se enruta a dsh por el puente Groq, pero no se ejecuta desde
  aquí (dsh es interactivo y se queda sin TPM en la 2ª llamada).
  Con --solo-enrutar solo dice a quién le tocaría y con qué comando.

Las claves nunca pasan por este archivo: los clientes de los conectores
las resuelven solos.

Uso:
    python3 sanguijuela.py --tipo texto|texto-largo|lectura|codigo \
        --tarea "..." [--solo-enrutar]
"""
import argparse
import subprocess
import sys

GEMINI_CLIENT = "/home/hatch/workspace/custom-connectors/custom.gemini/bin/client.py"
GROQ_CLIENT = "/home/hatch/workspace/custom-connectors/custom.groq/bin/client.py"
LEER = "/home/hatch/workspace/agente-cero-costo/puente-lectura/leer.py"

RUTAS = {
    "texto": ("Groq gpt-oss-20b", "texto corto, razonamiento, plan"),
    "texto-largo": ("Gemini gemini-3-flash-preview", "contexto grande"),
    "lectura": ("puente-lectura (Gemini + Groq)", "leer lo que no se abre"),
    "codigo": ("dsh por el puente Groq", "ejecutar código / agente"),
}


def llamar(cliente, args, prompt):
    r = subprocess.run(
        [sys.executable, cliente] + args + ["--prompt", prompt],
        capture_output=True, text=True, timeout=300,
    )
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip()[:300])
    return r.stdout.strip()


def cuenta(modelo, prompt, respuesta):
    # Estimación gruesa: ~4 caracteres por token.
    p = len(prompt) // 4
    r = len(respuesta) // 4
    print(f"\n--- cuenta ---")
    print(f"Trabajo pesado: {modelo}")
    print(f"Tokens aprox. del encargo: {p} (prompt) + {r} (respuesta)")
    print("El orquestador solo gastó la llamada y la verificación.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tipo", required=True,
                        choices=list(RUTAS))
    parser.add_argument("--tarea", required=True)
    parser.add_argument("--solo-enrutar", action="store_true")
    args = parser.parse_args()
    modelo, para = RUTAS[args.tipo]
    print(f"Enrutado: {modelo} ({para})")
    if args.solo_enrutar:
        if args.tipo == "codigo":
            print("Comando: cd ~/workspace/dsh-prueba && "
                  "DSH_DUMMY_KEY=dummy npx --yes @deepseek-ai/dsh "
                  "--profile headless --permission-mode workspace-write "
                  f"--approval-policy never \"{args.tarea}\"")
        else:
            print("Sin ejecutar: modo --solo-enrutar.")
        return
    if args.tipo == "codigo":
        print("El código se enruta a dsh pero no se ejecuta desde aquí: "
              "dsh es interactivo y se queda sin TPM en la 2ª llamada. "
              "Usa --solo-enrutar para ver el comando.")
        return
    if args.tipo == "texto":
        respuesta = llamar(GROQ_CLIENT,
                           ["chat", "--model", "openai/gpt-oss-20b"],
                           args.tarea)
    elif args.tipo == "texto-largo":
        respuesta = llamar(GEMINI_CLIENT,
                           ["generate", "--model", "gemini-3-flash-preview"],
                           args.tarea)
    elif args.tipo == "lectura":
        r = subprocess.run(
            [sys.executable, LEER, args.tarea],
            capture_output=True, text=True, timeout=900)
        if r.returncode != 0:
            raise RuntimeError((r.stderr or r.stdout).strip()[:300])
        respuesta = r.stdout.strip()
    print(respuesta)
    cuenta(modelo, args.tarea, respuesta)


if __name__ == "__main__":
    main()
