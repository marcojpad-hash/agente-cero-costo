#!/usr/bin/env python3
"""Generadores: de la definición canónica a cada harness.

Lee agents/sequential-verifiable/ (AGENT.md, workflow.md,
success-metrics.md, permissions.yaml) y genera:

- adapters/salida/claude.md  (Markdown para Claude Code)
- adapters/salida/codex.toml (TOML para Codex)
- adapters/salida/gemini.md  (Markdown para Gemini)

El formato TOML de Codex sigue el patrón de Agency Agents
(msitarzewski/agency-agents, MIT): una definición común que se
convierte por harness. Verificar el esquema TOML contra Codex antes
de usarlo en producción; la prueba (verificar.py) comprueba que las
instrucciones no se pierdan en la conversión, no la validez del
esquema.

Uso: python3 generar.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BASE = os.path.join(REPO, "agents", "sequential-verifiable")
SALIDA = os.path.join(HERE, "salida")


def leer(nombre):
    with open(os.path.join(BASE, nombre), encoding="utf-8") as f:
        return f.read()


def limpiar_md(texto):
    """Quita el título de primer nivel para reutilizar el cuerpo."""
    return re.sub(r"^# .*\n", "", texto, count=1).strip()


def generar_claude(agent, workflow, metrics, permissions):
    return (
        "# sequential-verifiable (Claude Code)\n\n"
        "Definición canónica generada desde "
        "agents/sequential-verifiable/. No editar a mano: editar la "
        "definición canónica y regenerar.\n\n"
        + agent + "\n\n## Workflow\n\n" + workflow
        + "\n\n## Criterios de éxito\n\n" + metrics
        + "\n\n## Permisos\n\n```yaml\n" + permissions + "```\n"
    )


def generar_gemini(agent, workflow, metrics, permissions):
    return (
        "# sequential-verifiable (Gemini)\n\n"
        "Definición canónica generada desde "
        "agents/sequential-verifiable/. No editar a mano: editar la "
        "definición canónica y regenerar.\n\n"
        + agent + "\n\n## Workflow\n\n" + workflow
        + "\n\n## Criterios de éxito\n\n" + metrics
        + "\n\n## Permisos\n\n```yaml\n" + permissions + "```\n"
    )


def generar_codex(agent, workflow, metrics, permissions):
    cuerpo = limpiar_md(agent)
    pasos = limpiar_md(workflow)
    criterios = limpiar_md(metrics)
    # TOML: cadenas multilínea literales (''' ''') para no escapar nada.
    return (
        "# sequential-verifiable (Codex)\n"
        "# Generado desde agents/sequential-verifiable/. No editar a mano.\n\n"
        '[agent]\n'
        'name = "sequential-verifiable"\n'
        'description = "Ejecuta un contrato de trabajo paso a paso y '
        'deja un resultado verificable en cada paso."\n\n'
        '[agent.instructions]\n'
        "definicion = '''\n" + cuerpo + "\n'''\n"
        "workflow = '''\n" + pasos + "\n'''\n"
        "criterios_exito = '''\n" + criterios + "\n'''\n\n"
        '[agent.permissions]\n'
        'guardar_secretos_en_repos = false\n'
        'leer_o_copiar_claves_de_la_boveda = false\n'
        'publicar_contenido_privado = false\n'
        'montar_mp4_oficial_capcot = false\n'
        'publicar_en_youtube_tiktok_facebook = false\n'
    )


def main():
    agent = leer("AGENT.md")
    workflow = leer("workflow.md")
    metrics = leer("success-metrics.md")
    permissions = leer("permissions.yaml")
    os.makedirs(SALIDA, exist_ok=True)
    salidas = {
        "claude.md": generar_claude(agent, workflow, metrics, permissions),
        "codex.toml": generar_codex(agent, workflow, metrics, permissions),
        "gemini.md": generar_gemini(agent, workflow, metrics, permissions),
    }
    for nombre, contenido in salidas.items():
        ruta = os.path.join(SALIDA, nombre)
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)
        print(f"{nombre}: {len(contenido)} bytes")


if __name__ == "__main__":
    main()
