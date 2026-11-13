"""Append-only JSONL evidence ledger and nested execution context."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Iterator
import hashlib
import json
import os
import threading
import uuid

_COMPONENT: ContextVar[str | None] = ContextVar("guardia_component", default=None)
_RUN_ID: ContextVar[str | None] = ContextVar("guardia_run_id", default=None)
_PARENT_RUN_ID: ContextVar[str | None] = ContextVar("guardia_parent_run_id", default=None)
_DEFAULT_LEDGER: "Ledger | None" = None
_LOCK = threading.RLock()


def nuevo_id() -> str:
    return str(uuid.uuid4())


def sha256_archivos(root: str | Path, paths: list[str | Path] | tuple[str | Path, ...]) -> str:
    base = Path(root).resolve()
    digest = hashlib.sha256()
    found = False
    for item in sorted((Path(p) for p in paths), key=lambda p: str(p)):
        path = item if item.is_absolute() else base / item
        if not path.exists():
            continue
        candidates = sorted(path.rglob("*")) if path.is_dir() else [path]
        for candidate in candidates:
            if not candidate.is_file():
                continue
            found = True
            try:
                relative = candidate.resolve().relative_to(base).as_posix()
            except ValueError:
                relative = candidate.name
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            with candidate.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            digest.update(b"\0")
    if not found:
        digest.update(b"EMPTY_INPUT_SET")
    return digest.hexdigest()


class Ledger:
    """Writes one JSON object per line. Existing records are never rewritten."""

    def __init__(self, path: str | Path, root: str | Path = ".") -> None:
        self.path = Path(path)
        self.root = Path(root).resolve()

    def append(
        self,
        event: str,
        component: str,
        *,
        status: str,
        run_id: str | None = None,
        parent_run_id: str | None = None,
        metadata_control: dict[str, Any] | None = None,
        facets: dict[str, Any] | None = None,
        payload_negocio: Any = None,
    ) -> dict[str, Any]:
        if event not in {"START", "COMPLETE", "FAIL"}:
            raise ValueError("event must be START, COMPLETE or FAIL")
        current = dict(metadata_control or {})
        timestamp = datetime.now(timezone.utc).isoformat()
        rid = run_id or _RUN_ID.get() or nuevo_id()
        parent = parent_run_id if parent_run_id is not None else _PARENT_RUN_ID.get()
        current.update({
            "timestamp": timestamp,
            "run_id": rid,
            "parent_run_id": parent,
            "component": component,
            "stage": event,
            "status": status,
        })
        record = {
            "run_id": rid,
            "parent_run_id": parent,
            "timestamp": timestamp,
            "component": component,
            "event": event,
            "metadata_control": current,
            "facets": facets or {},
            "payload_negocio": payload_negocio,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, ensure_ascii=False, sort_keys=True, default=str)
        with _LOCK:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
                handle.flush()
                os.fsync(handle.fileno())
        return record

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid ledger JSON at line {number}: {exc}") from exc
                if isinstance(value, dict):
                    records.append(value)
        return records


def configurar_ledger(path: str | Path, root: str | Path = ".") -> Ledger:
    global _DEFAULT_LEDGER
    _DEFAULT_LEDGER = Ledger(path, root)
    return _DEFAULT_LEDGER


@contextmanager
def componente(
    component: str,
    ledger: Ledger | None = None,
    *,
    input_paths: list[str] | None = None,
    output_paths: list[str] | None = None,
    evidence: str | None = None,
    origin: str = "python",
    payload_negocio: Any = None,
) -> Iterator[str]:
    target = ledger or _DEFAULT_LEDGER
    if target is None:
        raise RuntimeError("configure a ledger before using componente()")
    run_id = nuevo_id()
    parent_run_id = _RUN_ID.get()
    token_component = _COMPONENT.set(component)
    token_parent = _PARENT_RUN_ID.set(parent_run_id)
    token_run = _RUN_ID.set(run_id)
    inputs = sha256_archivos(target.root, input_paths or [])
    target.append(
        "START",
        component,
        status="STARTED",
        run_id=run_id,
        parent_run_id=parent_run_id,
        metadata_control={
            "origin": origin,
            "input_sha256": inputs,
            "evidence": evidence,
        },
        facets={"execution_identity": {"pid": os.getpid()}},
        payload_negocio=payload_negocio,
    )
    try:
        yield run_id
    except BaseException as exc:
        target.append(
            "FAIL",
            component,
            status="FALLO_EJECUCION",
            run_id=run_id,
            parent_run_id=parent_run_id,
            metadata_control={
                "origin": origin,
                "input_sha256": inputs,
                "motivo": "EXCEPTION",
                "reason": str(exc),
                "evidence": evidence,
            },
            facets={"error_details": {"type": type(exc).__name__, "message": str(exc)}},
            payload_negocio=payload_negocio,
        )
        raise
    else:
        output_hash = sha256_archivos(target.root, output_paths or [])
        target.append(
            "COMPLETE",
            component,
            status="EJECUTADO",
            run_id=run_id,
            parent_run_id=parent_run_id,
            metadata_control={
                "origin": origin,
                "input_sha256": inputs,
                "output_sha256": output_hash,
                "artifact_hash": output_hash,
                "evidence": evidence,
            },
            facets={"execution_identity": {"pid": os.getpid()}},
            payload_negocio=payload_negocio,
        )
    finally:
        _RUN_ID.reset(token_run)
        _PARENT_RUN_ID.reset(token_parent)
        _COMPONENT.reset(token_component)


def pieza(component: str, **options: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator form of componente()."""

    def decorate(function: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(function)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            with componente(component, **options):
                return function(*args, **kwargs)
        return wrapped
    return decorate
