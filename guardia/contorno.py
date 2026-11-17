"""Classify obstacles and propose a different next route without closing work."""

from __future__ import annotations

from typing import Any


_ROUTES = {
    "integrity": [
        "recompute the artifact from the recorded input and compare hashes",
        "locate the immutable source by its recorded identifier",
        "request a fresh source artifact and preserve both versions",
    ],
    "path": [
        "resolve the path from the repository root and enumerate exact matches",
        "inspect the parent directory and correct only the verified path",
        "request the missing artifact from its owner without fabricating it",
    ],
    "dependency": [
        "inspect the declared dependency files and identify the missing distribution",
        "use an already installed compatible package if it is explicitly allowed",
        "request approval for a new dependency before changing the environment",
    ],
    "permission": [
        "retry through an already authorized identity with the same scope",
        "use a repository-local fallback that preserves the evidence",
        "request the minimum missing permission from the owner",
    ],
    "contract": [
        "compare the observed output with the declared schema and list missing fields",
        "inspect one upstream artifact to identify the contract boundary",
        "request an explicit contract decision before interpreting the payload",
    ],
    "unknown": [
        "capture the exact failing command and its final diagnostic lines",
        "isolate the smallest reproducible component in a temporary workspace",
        "escalate with the evidence bundle and do not repeat the same attempt",
    ],
}


def clasificar_obstaculo(error: str) -> str:
    value = (error or "").lower()
    if any(term in value for term in ("sha256", "hash mismatch", "checksum", "integrity")):
        return "integrity"
    if any(term in value for term in ("no such file", "file not found", "path not found", "enoent")):
        return "path"
    if any(term in value for term in ("modulenotfound", "importerror", "dependency", "package not found")):
        return "dependency"
    if any(term in value for term in ("permission denied", "unauthorized", "forbidden", "http 401", "http 403")):
        return "permission"
    if any(term in value for term in ("schema", "contract", "missing key", "invalid field")):
        return "contract"
    return "unknown"


def siguiente_contorno(error: str, historial: list[dict[str, Any]] | None = None, max_intentos: int = 3) -> dict[str, Any]:
    history = historial or []
    category = clasificar_obstaculo(error)
    used = {str(item.get("accion")) for item in history}
    attempt = len(history) + 1
    if attempt > max_intentos:
        return {
            "categoria": category,
            "tipo_obstaculo": "piedra",
            "ruta_siguiente": "agua",
            "intento": attempt,
            "accion": "ESCALAR_CON_EVIDENCIA",
            "escalar": True,
            "marca_ok": False,
            "cierra_orden": False,
        }
    choices = _ROUTES[category]
    action = next((choice for choice in choices if choice not in used), None)
    if action is None:
        return {
            "categoria": category,
            "intento": attempt,
            "accion": "ESCALAR_CON_EVIDENCIA",
            "escalar": True,
            "marca_ok": False,
            "cierra_orden": False,
        }
    return {
        "categoria": category,
        "tipo_obstaculo": "piedra",
        "ruta_siguiente": "agua",
        "intento": attempt,
        "accion": action,
        "escalar": False,
        "marca_ok": False,
        "cierra_orden": False,
    }
