"""Configuration-driven execution, evidence validation and five-state gate."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import fnmatch
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys

from .contorno import siguiente_contorno
from .ledger import Ledger, nuevo_id, sha256_archivos

ESTADOS = (
    "OK_CON_EVIDENCIA",
    "INFO_CORRIO_SIN_SENAL",
    "INFO_OMISION_CONTRACTUAL",
    "FALLO_EJECUCION",
    "REQUIERE_CONTRATO",
)
FALLOS = {
    "SIMULADO_FIXTURE", "API_PENDING", "APAGADA_POR_FLAG", "NO_INVOCADO",
    "OMITIDO_SIN_CONTRATO", "REPORTED_EXECUTED_NOT_OBSERVED",
    "OUTPUT_PERSISTED_WITHOUT_CONSUMER", "PACKAGE_NOT_ALLOWED",
    "INTENTADO_FALLIDO", "SIN_EVIDENCIA", "ARTIFACT_MISSING",
    "ARTIFACT_EMPTY", "HASH_MISSING",
}
OMISIONES = {"NOT_APPLICABLE", "NO_APLICA", "OMISION_CONTRATUAL"}
SENAL_AUSENTE = {"CORRIO_SIN_SENAL", "SIN_SENAL"}
_PACKAGE_RE = re.compile(r"^([A-Za-z0-9_.-]+)")


def _normalizar_paquete(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value.strip().lower())


def cargar_configuracion(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("configuration root must be an object")
    for key in ("security", "gatekeeper", "topology"):
        if not isinstance(data.get(key), dict):
            raise ValueError(f"configuration requires object: {key}")
    gate = data["gatekeeper"]
    gate.setdefault("exit_code_on_fail", 9)
    gate.setdefault("strict_mode_env_var", "GUARDIA_ESTRICTA")
    gate.setdefault("strict_mode_default", True)
    gate.setdefault("exclude_sidecars", ["*.log", "*.jsonl", "*.tmp", "*.pyc"])
    specs = data["topology"].get("expected_components")
    if not isinstance(specs, dict):
        raise ValueError("topology.expected_components must be an object")
    for name, spec in specs.items():
        if not isinstance(spec, dict):
            raise ValueError(f"component definition must be an object: {name}")
        spec.setdefault("required", True)
        spec.setdefault("terminal", False)
        spec.setdefault("feeds", [])
        spec.setdefault("consumes", [])
        spec.setdefault("requires_input", False)
        spec.setdefault("expected_artifacts", [])
        spec.setdefault("expected_keys_in_output", {})
    return data


def _strict_mode(config: dict[str, Any]) -> tuple[bool, str]:
    name = str(config["gatekeeper"].get("strict_mode_env_var", "GUARDIA_ESTRICTA"))
    value = os.getenv(name)
    if value is None:
        return bool(config["gatekeeper"].get("strict_mode_default", True)), name
    return value.strip() != "0", name


def _changed_files(root: Path) -> list[str]:
    base = os.getenv("GUARDIA_BASE_SHA", "").strip()
    head = os.getenv("GUARDIA_HEAD_SHA", "").strip() or "HEAD"
    if not base or set(base) == {"0"}:
        return []
    result = subprocess.run(
        ["git", "diff", "--name-only", base, head],
        cwd=root, capture_output=True, text=True, check=False,
    )
    return sorted(line.strip() for line in result.stdout.splitlines() if line.strip()) if result.returncode == 0 else []


def _tests_present(root: Path) -> bool:
    return any(p.is_dir() for p in root.rglob("tests") if ".git" not in p.parts and ".guardia" not in p.parts)


def _smoke_files(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*")
        if p.is_file() and ".git" not in p.parts and ".guardia" not in p.parts
        and (
            p.name == "supervisor.smoke"
            or (p.name.startswith("smoke") and p.suffix in {".sh", ".py"})
            or ("smoke" in p.stem.lower() and p.suffix == ".py")
        )
    )


def _requirements(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("requirements*.txt") if ".git" not in p.parts and ".guardia" not in p.parts)


def _package_policy(root: Path, config: dict[str, Any]) -> tuple[bool, list[str], str]:
    allowed = {_normalizar_paquete(str(x)) for x in config["security"].get("allowed_packages", [])}
    files = _requirements(root)
    if not files:
        return True, [], "NO_REQUIREMENTS_FILES"
    if "*" in allowed:
        return True, [], "ALLOW_ALL_DECLARED"
    declared: set[str] = set()
    for path in files:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            value = line.strip()
            if not value or value.startswith(("#", "-")):
                continue
            match = _PACKAGE_RE.match(value)
            if match:
                declared.add(_normalizar_paquete(match.group(1)))
    rejected = sorted(declared - allowed)
    return not rejected, rejected, "PACKAGE_ALLOWLIST"


def _when_applies(when: str, root: Path, changed: list[str]) -> bool:
    if when in ("", "always"):
        return True
    if when == "changed_python_files":
        return any(name.endswith(".py") for name in changed)
    if when == "tests_present":
        return _tests_present(root)
    if when == "smokes_present":
        return bool(_smoke_files(root))
    if when == "requirements_present":
        return bool(_requirements(root))
    if when.startswith("path_exists:"):
        return (root / when.split(":", 1)[1]).exists()
    raise ValueError(f"unknown condition: {when}")


def _within_root(root: Path, value: str, fail_outside: bool) -> Path:
    candidate = (root / value).resolve()
    if fail_outside and not candidate.is_relative_to(root.resolve()):
        raise ValueError(f"artifact path outside repository root: {value}")
    return candidate


def _is_sidecar(path: Path, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path.name, pattern) for pattern in patterns)


def _check_artifacts(root: Path, spec: dict[str, Any], config: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    gate = config["gatekeeper"]
    fail_outside = bool(config["security"].get("fail_on_outside_artifact", True))
    sidecars = list(gate.get("exclude_sidecars", []))
    for pattern in spec.get("expected_artifacts", []):
        candidate = _within_root(root, str(pattern), fail_outside)
        matches = sorted(root.glob(str(pattern))) if any(char in str(pattern) for char in "*?[") else [candidate]
        valid = [
            p for p in matches
            if p.exists() and p.is_file() and p.stat().st_size > 0 and not _is_sidecar(p, sidecars)
        ]
        if not valid:
            problems.append(f"ARTIFACT_MISSING_OR_EMPTY:{pattern}")
    for artifact, keys in spec.get("expected_keys_in_output", {}).items():
        path = _within_root(root, str(artifact), fail_outside)
        if not path.is_file() or path.stat().st_size == 0 or _is_sidecar(path, sidecars):
            problems.append(f"ARTIFACT_MISSING:{artifact}")
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            problems.append(f"ARTIFACT_NOT_JSON:{artifact}")
            continue
        if not isinstance(value, dict) or any(key not in value for key in keys):
            problems.append(f"EXPECTED_KEYS_MISSING:{artifact}")
    return problems


def _run_builtin(name: str, root: Path, changed: list[str], config: dict[str, Any]) -> tuple[int, str, str]:
    if name == "compile_changed_python":
        files = [item for item in changed if item.endswith(".py")]
        if not files:
            return 0, "No changed Python files.\n", "NOT_APPLICABLE"
        result = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", *files],
            cwd=root, capture_output=True, text=True, check=False,
        )
        return result.returncode, result.stdout, result.stderr
    if name == "placeholder_scan":
        files = [item for item in changed if item.endswith(".py")]
        findings = []
        for item in files:
            path = root / item
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            marker = "PLACE" + "HOLDER"
            todo_marker = "TODO_" + marker
            if marker in text or todo_marker in text:
                findings.append(f"{marker}:{item}")
        return (1, "", "\n".join(findings)) if findings else (0, f"Scanned {len(files)} changed Python files.\n", "")
    if name == "size_delta":
        base = os.getenv("GUARDIA_BASE_SHA", "").strip()
        if not base or set(base) == {"0"}:
            return 0, "No previous revision available for size comparison.\n", "CORRIO_SIN_SENAL"
        findings = []
        for item in changed:
            if not item.endswith(".py"):
                continue
            path = root / item
            if not path.is_file():
                continue
            previous = subprocess.run(
                ["git", "show", f"{base}:{item}"], cwd=root,
                capture_output=True, check=False,
            )
            if previous.returncode != 0:
                continue
            old_size = len(previous.stdout)
            new_size = path.stat().st_size
            if old_size > 0 and new_size < old_size * 0.8:
                findings.append(f"SIZE_DROP_OVER_20_PERCENT:{item}:{old_size}->{new_size}")
        return (1, "", "\n".join(findings)) if findings else (0, "No changed Python file lost more than 20% of its previous size.\n", "")
    if name == "package_policy":
        okay, rejected, reason = _package_policy(root, config)
        if reason == "NO_REQUIREMENTS_FILES":
            return 0, "No dependency manifests; policy not applicable.\n", "NOT_APPLICABLE"
        if not okay:
            return 1, "", "PACKAGE_NOT_ALLOWED:" + ",".join(rejected)
        return 0, f"Declared dependencies are allowlisted ({reason}).\n", ""
    if name == "tests":
        if not _tests_present(root):
            return 0, "No tests directory.\n", "NOT_APPLICABLE"
        if importlib.util.find_spec("pytest") is not None:
            command = [sys.executable, "-m", "pytest", "-q"]
        else:
            command = [sys.executable, "-m", "unittest", "discover", "-s", ".", "-p", "test*.py"]
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
        output = result.stdout + result.stderr
        if result.returncode == 0 and re.search(r"Ran 0 tests|no tests ran", output, re.I):
            return 0, output, "CORRIO_SIN_SENAL"
        return result.returncode, result.stdout, result.stderr
    if name == "smokes":
        files = _smoke_files(root)
        if not files:
            return 0, "No smoke scripts.\n", "NOT_APPLICABLE"
        stdout: list[str] = []
        stderr: list[str] = []
        for path in files:
            command = [sys.executable, str(path.relative_to(root))] if path.suffix == ".py" else ["bash", str(path.relative_to(root))]
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
            stdout.append(f"$ {' '.join(command)}\n{result.stdout}")
            stderr.append(result.stderr)
            if result.returncode != 0:
                return result.returncode, "".join(stdout), "".join(stderr)
        return 0, "".join(stdout), "".join(stderr)
    raise ValueError(f"unknown builtin: {name}")


def _event_state(event: dict[str, Any], spec: dict[str, Any]) -> tuple[str, str]:
    control = event.get("metadata_control")
    if not isinstance(control, dict):
        return "REQUIERE_CONTRATO", "METADATA_CONTROL_MISSING"
    status = str(control.get("status", "")).upper()
    event_type = str(event.get("event", "")).upper()
    if event_type == "FAIL" or status in FALLOS:
        return "FALLO_EJECUCION", status or "EVENT_FAIL"
    if status == "REQUIERE_CONTRATO":
        return "REQUIERE_CONTRATO", status
    if status in OMISIONES:
        return "INFO_OMISION_CONTRACTUAL", status
    if status in SENAL_AUSENTE:
        return "INFO_CORRIO_SIN_SENAL", status
    if event_type == "COMPLETE" and status in {"EJECUTADO", "OK", "OK_CON_EVIDENCIA"}:
        if spec.get("requires_input") and not control.get("input_sha256"):
            return "FALLO_EJECUCION", "INPUT_HASH_MISSING"
        if not control.get("evidence"):
            return "FALLO_EJECUCION", "EVIDENCE_MISSING"
        if not control.get("output_sha256"):
            return "FALLO_EJECUCION", "OUTPUT_HASH_MISSING"
        return "OK_CON_EVIDENCIA", "EVIDENCE_PRESENT"
    if event_type == "START":
        return "FALLO_EJECUCION", "REPORTED_EXECUTED_NOT_OBSERVED"
    return "REQUIERE_CONTRATO", status or "UNKNOWN_STATUS"


def evaluar(config: dict[str, Any], ledger: str | Path | list[dict[str, Any]], root: str | Path = ".") -> dict[str, Any]:
    base = Path(root).resolve()
    records = Ledger(ledger, base).read() if isinstance(ledger, (str, Path)) else list(ledger)
    specs = config["topology"]["expected_components"]
    results: dict[str, dict[str, Any]] = {}
    for component, spec in specs.items():
        events = [item for item in records if item.get("component") == component]
        if not events:
            state = "FALLO_EJECUCION" if spec.get("required", True) else "INFO_OMISION_CONTRACTUAL"
            results[component] = {"estado": state, "motivo": "NO_INVOCADO", "event": None}
            continue
        last = events[-1]
        state, reason = _event_state(last, spec)
        if state == "OK_CON_EVIDENCIA":
            problems = _check_artifacts(base, spec, config)
            if problems:
                state, reason = "FALLO_EJECUCION", ";".join(problems)
        results[component] = {"estado": state, "motivo": reason, "event": last}
    for component, spec in specs.items():
        feeds = spec.get("feeds", [])
        current = results.get(component, {})
        event = current.get("event")
        if not feeds or spec.get("terminal") or current.get("estado") != "OK_CON_EVIDENCIA" or not event:
            continue
        output_hash = (event.get("metadata_control") or {}).get("output_sha256")
        for consumer in feeds:
            consumer_result = results.get(consumer, {})
            consumer_event = consumer_result.get("event")
            if consumer_result.get("estado") != "OK_CON_EVIDENCIA" or not consumer_event:
                results[component] = {
                    "estado": "FALLO_EJECUCION",
                    "motivo": f"OUTPUT_PERSISTED_WITHOUT_CONSUMER:{consumer}",
                    "event": event,
                }
                break
            meta = consumer_event.get("metadata_control") or {}
            if component not in meta.get("consumes", []) and meta.get("input_sha256") != output_hash:
                results[component] = {
                    "estado": "FALLO_EJECUCION",
                    "motivo": f"OUTPUT_PERSISTED_WITHOUT_CONSUMER:{consumer}",
                    "event": event,
                }
                break
    counts = {state: sum(1 for value in results.values() if value["estado"] == state) for state in ESTADOS}
    return {
        "estados": results,
        "counts": counts,
        "failed": counts["FALLO_EJECUCION"] > 0,
        "exit_code_on_fail": int(config["gatekeeper"].get("exit_code_on_fail", 9)),
    }


def ejecutar_configuracion(
    config_path: str | Path = "guardia.config.json",
    ledger_path: str | Path = ".guardia/ledger.jsonl",
    report_path: str | Path = ".guardia/report.json",
    root: str | Path = ".",
) -> tuple[dict[str, Any], int]:
    base = Path(root).resolve()
    config_file = Path(config_path)
    if not config_file.is_absolute():
        config_file = base / config_file
    config = cargar_configuracion(config_file)
    ledger_file = Path(ledger_path)
    if not ledger_file.is_absolute():
        ledger_file = base / ledger_file
    report_file = Path(report_path)
    if not report_file.is_absolute():
        report_file = base / report_file
    ledger = Ledger(ledger_file, base)
    strict, strict_env = _strict_mode(config)
    workflow_run_id = nuevo_id()
    changed = _changed_files(base)
    stopped = False
    failed_component: str | None = None

    if not strict:
        ledger.append(
            "COMPLETE", "guardia.strict_mode", status="OMISION_CONTRATUAL",
            run_id=workflow_run_id,
            metadata_control={
                "origin": "guardia", "strict_mode": False,
                "motivo": f"{strict_env}=0; gate disabled explicitly",
                "evidence": os.getenv("GUARDIA_EVIDENCE_URL", "environment"),
                "output_sha256": hashlib.sha256(b"strict-mode-disabled").hexdigest(),
            },
        )

    for component, spec in config["topology"]["expected_components"].items():
        run_id = nuevo_id()
        when = str(spec.get("when", "always"))
        try:
            applies = _when_applies(when, base, changed)
        except ValueError as exc:
            ledger.append(
                "COMPLETE", component, status="REQUIERE_CONTRATO",
                run_id=run_id, parent_run_id=workflow_run_id,
                metadata_control={"origin": "guardia", "motivo": "UNKNOWN_CONDITION", "reason": str(exc)},
            )
            continue
        if not applies:
            ledger.append(
                "COMPLETE", component, status="NOT_APPLICABLE",
                run_id=run_id, parent_run_id=workflow_run_id,
                metadata_control={
                    "origin": "guardia", "motivo": "CONDITION_NOT_MET", "condition": when,
                    "evidence": os.getenv("GUARDIA_EVIDENCE_URL", "guardia.config.json"),
                    "input_sha256": sha256_archivos(base, []),
                    "output_sha256": hashlib.sha256(f"{component}:not-applicable".encode()).hexdigest(),
                    "consumes": spec.get("consumes", []),
                },
            )
            continue
        if stopped:
            ledger.append(
                "FAIL", component, status="NO_INVOCADO",
                run_id=run_id, parent_run_id=workflow_run_id,
                metadata_control={"origin": "guardia", "motivo": "FAIL_FAST", "blocked_by": failed_component},
            )
            continue

        log_dir = base / ".guardia" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{component}.log"
        input_paths = spec.get("input_paths", changed)
        input_hash = sha256_archivos(base, input_paths)
        ledger.append(
            "START", component, status="STARTED",
            run_id=run_id, parent_run_id=workflow_run_id,
            metadata_control={
                "origin": "guardia", "input_sha256": input_hash,
                "strict_mode": strict, "consumes": spec.get("consumes", []),
            },
            facets={"execution_identity": {"python": sys.version.split()[0], "pid": os.getpid()}},
        )
        try:
            builtin = spec.get("builtin")
            if builtin:
                return_code, stdout, stderr = _run_builtin(str(builtin), base, changed, config)
            else:
                command = spec.get("command")
                if not isinstance(command, list) or not command:
                    ledger.append(
                        "COMPLETE", component, status="REQUIERE_CONTRATO",
                        run_id=run_id, parent_run_id=workflow_run_id,
                        metadata_control={"origin": "guardia", "motivo": "COMMAND_NOT_DECLARED"},
                    )
                    continue
                expanded: list[str] = []
                for arg in command:
                    if arg == "${CHANGED_PY_FILES}":
                        expanded.extend(name for name in changed if name.endswith(".py"))
                    else:
                        expanded.append(str(arg).replace("${REPO_ROOT}", str(base)))
                result = subprocess.run(
                    expanded, cwd=base, capture_output=True, text=True, check=False,
                    timeout=int(spec.get("timeout_seconds", 300)),
                )
                return_code, stdout, stderr = result.returncode, result.stdout, result.stderr
            log_text = (stdout or "") + (stderr or "")
            if not log_text:
                log_text = f"completed with exit_code={return_code}\n"
            log_path.write_text(log_text, encoding="utf-8")
            evidence = os.getenv("GUARDIA_EVIDENCE_URL") or spec.get("evidence") or str(log_path.relative_to(base))
            output_paths = [str(item) for item in spec.get("expected_artifacts", [])] or [str(log_path.relative_to(base))]
            output_hash = sha256_archivos(base, output_paths)
            if stderr == "NOT_APPLICABLE":
                ledger.append(
                    "COMPLETE", component, status="NOT_APPLICABLE",
                    run_id=run_id, parent_run_id=workflow_run_id,
                    metadata_control={
                        "origin": "guardia", "input_sha256": input_hash,
                        "output_sha256": output_hash, "evidence": evidence,
                        "consumes": spec.get("consumes", []), "motivo": "CONDITIONALLY_NOT_APPLICABLE",
                    },
                )
            elif stderr == "CORRIO_SIN_SENAL" and return_code == 0:
                ledger.append(
                    "COMPLETE", component, status="CORRIO_SIN_SENAL",
                    run_id=run_id, parent_run_id=workflow_run_id,
                    metadata_control={
                        "origin": "guardia", "input_sha256": input_hash,
                        "output_sha256": output_hash, "evidence": evidence,
                        "consumes": spec.get("consumes", []),
                    },
                )
            elif return_code == 0:
                ledger.append(
                    "COMPLETE", component, status="EJECUTADO",
                    run_id=run_id, parent_run_id=workflow_run_id,
                    metadata_control={
                        "origin": "guardia", "input_sha256": input_hash,
                        "output_sha256": output_hash, "artifact_hash": output_hash,
                        "evidence": evidence, "consumes": spec.get("consumes", []),
                    },
                )
            else:
                ledger.append(
                    "FAIL", component, status="FALLO_EJECUCION",
                    run_id=run_id, parent_run_id=workflow_run_id,
                    metadata_control={
                        "origin": "guardia", "input_sha256": input_hash,
                        "output_sha256": output_hash, "evidence": evidence,
                        "motivo": "COMMAND_FAILED", "exit_code": return_code,
                    },
                    facets={"error_details": {"stderr_tail": log_text[-4000:]}},
                )
                failed_component = component
                stopped = strict
        except Exception as exc:
            log_path.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
            ledger.append(
                "FAIL", component, status="FALLO_EJECUCION",
                run_id=run_id, parent_run_id=workflow_run_id,
                metadata_control={
                    "origin": "guardia", "input_sha256": input_hash,
                    "motivo": type(exc).__name__, "reason": str(exc),
                },
                facets={"error_details": {"type": type(exc).__name__, "message": str(exc)}},
            )
            failed_component = component
            stopped = strict

    report = evaluar(config, ledger_file, base)
    report.update({
        "run_id": workflow_run_id,
        "strict_mode": strict,
        "strict_mode_env_var": strict_env,
        "changed_files": changed,
        "ledger_path": str(ledger_file.relative_to(base)) if ledger_file.is_relative_to(base) else str(ledger_file),
    })
    report["contornos"] = {}
    for component, value in report["estados"].items():
        if value["estado"] != "FALLO_EJECUCION":
            continue
        event = value.get("event") or {}
        facets = event.get("facets") or {}
        error = (facets.get("error_details") or {}).get("stderr_tail") or value["motivo"]
        report["contornos"][component] = siguiente_contorno(str(error))
    exit_code = int(config["gatekeeper"].get("exit_code_on_fail", 9)) if strict and report["failed"] else 0
    report["exit_code"] = exit_code
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    return report, exit_code
