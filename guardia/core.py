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
import uuid

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
    "SIMULADO_FIXTURE",
    "API_PENDING",
    "APAGADA_POR_FLAG",
    "NO_INVOCADO",
    "OMITIDO_SIN_CONTRATO",
    "REPORTED_EXECUTED_NOT_OBSERVED",
    "OUTPUT_PERSISTED_WITHOUT_CONSUMER",
    "PACKAGE_NOT_ALLOWED",
    "INTENTADO_FALLIDO",
    "SIN_EVIDENCIA",
    "ARTIFACT_MISSING",
    "ARTIFACT_EMPTY",
    "HASH_MISSING",
}
OMISIONES = {"NOT_APPLICABLE", "NO_APLICA", "OMISION_CONTRATUAL"}
SENAL_AUSENTE = {"CORRIO_SIN_SENAL", "SIN_SENAL"}
NORMALIZE = re.compile(r"[-_.]+")


def _normalizar_paquete(value: str) -> str:
    return NORMALIZE.sub("-", value.strip().lower())


def cargar_configuracion(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("configuration root must be an object")
    for key in ("security", "gatekeeper", "topology"):
        if not isinstance(data.get(key), dict):
            raise ValueError(f"configuration requires object: {key}")
    gate = data["gatekeeper"]
    gate.setdefault("exit_code_on_fail", 9)
    gate.setdefault("strict_mode_env_var", "GUARDIA_ESTRICTA")
    gate.setdefault("strict_mode_default", True)
    gate.setdefault("exclude_sidecars", ["*.log", "*.jsonl", "*.tmp"])
    topology = data["topology"].get("expected_components")
    if not isinstance(topology, dict):
        raise ValueError("topology.expected_components must be an object")
    for component, spec in topology.items():
        if not isinstance(spec, dict):
            raise ValueError(f"component definition must be an object: {component}")
        spec.setdefault("required", True)
        spec.setdefault("terminal", False)
        spec.setdefault("feeds", [])
        spec.setdefault("requires_input", False)
        spec.setdefault("expected_artifacts", [])
        spec.setdefault("expected_keys_in_output", {})
    return data


def _strict_mode(config: dict[str, Any]) -> tuple[bool, str]:
    gate = config["gatekeeper"]
    name = str(gate.get("strict_mode_env_var", "GUARDIA_ESTRICTA"))
    value = os.getenv(name)
    if value is None:
        return bool(gate.get("strict_mode_default", True)), name
    return value.strip() != "0", name


def _changed_files(root: Path) -> list[str]:
    base = os.getenv("GUARDIA_BASE_SHA", "").strip()
    head = os.getenv("GUARDIA_HEAD_SHA", "").strip() or "HEAD"
    if not base or set(base) == {"0"}:
        return []
    result = subprocess.run(
        ["git", "diff", "--name-only", base, head],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return sorted(line.strip() for line in result.stdout.splitlines() if line.strip())


def _has_tests(root: Path) -> bool:
    return any(path.is_dir() for path in root.rglob("tests") if ".git" not in path.parts and ".guardia" not in path.parts)


def _smoke_files(root: Path) -> list[Path]:
    return sorted(
        path for path in root.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and ".guardia" not in path.parts
        and (path.name.startswith("smoke") and path.suffix == ".sh" or path.name.endswith("smoke.py"))
    )


def _requirements(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("requirements*.txt") if ".git" not in path.parts and ".guardia" not in path.parts)


def _package_policy(root: Path, config: dict[str, Any]) -> tuple[bool, list[str], str]:
    allowed = {_normalizar_paquete(str(item)) for item in config["security"].get("allowed_packages", [])}
    requirement_files = _requirements(root)
    if not requirement_files:
        return True, [], "NO_REQUIREMENTS_FILES"
    if "*" in allowed:
        return True, [], "ALLOW_ALL_DECLARED"
    declared: set[str] = set()
    for path in requirement_files:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            value = line.strip()
            if not value or value.startswith(("#", "-")):
                continue
            match = re.match(r"([A-Za-z0-9_.-]+)", value)
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
        return _has_tests(root)
    if when == "smokes_present":
        return bool(_smoke_files(root))
    if when == "requirements_present":
        return bool(_requirements(root))
    if when.startswith("path_exists:"):
        return (root / when.split(":", 1)[1]).exists()
    raise ValueError(f"unknown condition: {when}")


def _within_root(root: Path, value: str) -> Path:
    candidate = (root / value).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError(f"artifact path outside repository root: {value}")
    return candidate


def _check_artifacts(root: Path, spec: dict[str, Any], config: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    for pattern in spec.get("expected_artifacts", []):
        candidate = _within_root(root, str(pattern))
        matches = sorted(root.glob(str(pattern))) if any(char in str(pattern) for char in "*?[") else [candidate]
        valid = [path for path in matches if path.exists() and path.is_file() and path.stat().st_size > 0]
        if not valid:
            problems.append(f"ARTIFACT_MISSING_OR_EMPTY:{pattern}")
    for artifact, keys in spec.get("expected_keys_in_output", {}).items():
        path = _within_root(root, str(artifact))
        if not path.is_file() or path.stat().st_size == 0:
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


def _run_builtin(name: str, root: Path, changed: list[str]) -> tuple[int, str, str]:
    if name == "compile_changed_python":
        files = [item for item in changed if item.endswith(".py")]
        if not files:
            return 0, "No changed Python files; compile step not applicable.\n", "NOT_APPLICABLE"
        command = [sys.executable, "-m", "compileall", "-q", *files]
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
        return result.returncode, result.stdout, result.stderr
    if name == "tests":
        if not _has_tests(root):
            return 0, "No tests directory; contractually omitted.\n", "NOT_APPLICABLE"
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
            return 0, "No smoke scripts; contractually omitted.\n", "NOT_APPLICABLE"
        out: list[str] = []
        err: list[str] = []
        for path in files:
            command = ["bash", str(path.relative_to(root))] if path.suffix == ".sh" else [sys.executable, str(path.relative_to(root))]
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
            out.append(f"$ {' '.join(command)}\n{result.stdout}")
            err.append(result.stderr)
            if result.returncode != 0:
                return result.returncode, "".join(out), "".join(err)
        return 0, "".join(out), "".join(err)
    if name == "package_policy":
        return 0, "Package policy evaluated by the guard.\n", ""
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
            consumes = meta.get("consumes", [])
            if component not in consumes and meta.get("input_sha256") != output_hash:
                results[component] = {
                    "estado": "FALLO_EJECUCION",
                    "motivo": f"OUTPUT_PERSISTED_WITHOUT_CONSUMER:{consumer}",
                    "event": event,
                }
                break
    counts = {state: sum(1 for value in results.values() if value["estado"] == state) for state in ESTADOS}
    failed = counts["FALLO_EJECUCION"] > 0
    return {
        "estados": results,
        "counts": counts,
        "failed": failed,
        "strict_mode": None,
        "exit_code_on_fail": int(config["gatekeeper"].get("exit_code_on_fail", 9)),
    }


def ejecutar_configuracion(
    config_path: str | Path = "guardia.config.json",
    ledger_path: str | Path = ".guardia/ledger.jsonl",
    report_path: str | Path = ".guardia/report.json",
    root: str | Path = ".",
) -> tuple[dict[str, Any], int]:
    base = Path(root).resolve()
    config = cargar_configuracion(config_path if Path(config_path).is_absolute() else base / config_path)
    ledger_file = ledger_path if Path(ledger_path).is_absolute() else base / ledger_path
    report_file = report_path if Path(report_path).is_absolute() else base / report_path
    ledger = Ledger(ledger_file, base)
    strict, strict_env = _strict_mode(config)
    workflow_run_id = nuevo_id()
    changed = _changed_files(base)
    specs = config["topology"]["expected_components"]
    stopped = False
    previous_failure: str | None = None

    policy_ok, rejected, policy_reason = _package_policy(base, config)
    if policy_reason != "NO_REQUIREMENTS_FILES":
        component = "dependency_policy"
        run_id = nuevo_id()
        ledger.append(
            "START", component, status="STARTED", run_id=run_id, parent_run_id=workflow_run_id,
            metadata_control={"origin": "guardia", "input_sha256": sha256_archivos(base, _requirements(base)), "strict_mode": strict},
        )
        if policy_ok:
            ledger.append(
                "COMPLETE", component, status="EJECUTADO", run_id=run_id, parent_run_id=workflow_run_id,
                metadata_control={
                    "origin": "guardia", "input_sha256": sha256_archivos(base, _requirements(base)),
                    "output_sha256": hashlib.sha256(json.dumps(sorted(config["security"].get("allowed_packages", []))).encode()).hexdigest(),
                    "evidence": os.getenv("GUARDIA_EVIDENCE_URL", "guardia.config.json"),
                    "consumes": [],
                },
            )
        else:
            ledger.append(
                "FAIL", component, status="PACKAGE_NOT_ALLOWED", run_id=run_id, parent_run_id=workflow_run_id,
                metadata_control={"origin": "guardia", "motivo": "PACKAGE_NOT_ALLOWED", "reason": ",".join(rejected)},
                facets={"error_details": {"rejected_packages": rejected}},
            )
            previous_failure = component
            stopped = strict

    for component, spec in specs.items():
        run_id = nuevo_id()
        when = str(spec.get("when", "always"))
        try:
            applies = _when_applies(when, base, changed)
        except ValueError as exc:
            applies = True
            ledger.append(
                "FAIL", component, status="REQUIERE_CONTRATO", run_id=run_id, parent_run_id=workflow_run_id,
                metadata_control={"origin": "guardia", "motivo": "UNKNOWN_CONDITION", "reason": str(exc)},
            )
            previous_failure = component
            stopped = strict
            continue
        if stopped:
            ledger.append(
                "FAIL", component, status="NO_INVOCADO", run_id=run_id, parent_run_id=workflow_run_id,
                metadata_control={"origin": "guardia", "motivo": "FAIL_FAST", "blocked_by": previous_failure},
            )
            continue
        if not applies:
            ledger.append(
                "COMPLETE", component, status="NOT_APPLICABLE", run_id=run_id, parent_run_id=workflow_run_id,
                metadata_control={
                    "origin": "guardia", "motivo": "CONDITION_NOT_MET", "condition": when,
                    "evidence": os.getenv("GUARDIA_EVIDENCE_URL", "guardia.config.json"),
                    "input_sha256": sha256_archivos(base, changed),
                    "output_sha256": hashlib.sha256(f"{component}:not-applicable".encode()).hexdigest(),
                },
            )
            continue

        log_dir = base / ".guardia" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{component}.log"
        input_hash = sha256_archivos(base, changed)
        ledger.append(
            "START", component, status="STARTED", run_id=run_id, parent_run_id=workflow_run_id,
            metadata_control={
                "origin": "guardia", "input_sha256": input_hash, "strict_mode": strict,
                "consumes": spec.get("consumes", []),
            },
            facets={"execution_identity": {"python": sys.version.split()[0], "pid": os.getpid()}},
        )
        try:
            builtin = spec.get("builtin")
            if builtin:
                return_code, stdout, stderr = _run_builtin(str(builtin), base, changed)
            else:
                command = spec.get("command")
                if not isinstance(command, list) or not command:
                    raise ValueError("component requires a builtin or a non-empty command array")
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
            log_path.write_text((stdout or "") + (stderr or ""), encoding="utf-8")
            evidence = os.getenv("GUARDIA_EVIDENCE_URL") or str(log_path.relative_to(base))
            output_paths = [str(path) for path in spec.get("expected_artifacts", [])]
            if not output_paths:
                output_paths = [str(log_path.relative_to(base))]
            output_hash = sha256_archivos(base, output_paths)
            if stderr == "NOT_APPLICABLE":
                status = "NOT_APPLICABLE"
                ledger.append(
                    "COMPLETE", component, status=status, run_id=run_id, parent_run_id=workflow_run_id,
                    metadata_control={
                        "origin": "guardia", "input_sha256": input_hash, "output_sha256": output_hash,
                        "evidence": evidence, "consumes": spec.get("consumes", []),
                        "motivo": "CONDITIONALLY_NOT_APPLICABLE",
                    },
                )
            elif stderr == "CORRIO_SIN_SENAL" and return_code == 0:
                ledger.append(
                    "COMPLETE", component, status="CORRIO_SIN_SENAL", run_id=run_id, parent_run_id=workflow_run_id,
                    metadata_control={
                        "origin": "guardia", "input_sha256": input_hash, "output_sha256": output_hash,
                        "evidence": evidence, "consumes": spec.get("consumes", []),
                    },
                )
            elif return_code == 0:
                ledger.append(
                    "COMPLETE", component, status="EJECUTADO", run_id=run_id, parent_run_id=workflow_run_id,
                    metadata_control={
                        "origin": "guardia", "input_sha256": input_hash, "output_sha256": output_hash,
                        "artifact_hash": output_hash, "evidence": evidence,
                        "consumes": spec.get("consumes", []),
                    },
                )
            else:
                ledger.append(
                    "FAIL", component, status="FALLO_EJECUCION", run_id=run_id, parent_run_id=workflow_run_id,
                    metadata_control={
                        "origin": "guardia", "input_sha256": input_hash, "output_sha256": output_hash,
                        "evidence": evidence, "motivo": "COMMAND_FAILED", "exit_code": return_code,
                    },
                    facets={"error_details": {"stderr_tail": (stderr or stdout)[-4000:]}},
                )
                previous_failure = component
                stopped = strict
        except Exception as exc:
            log_path.write_text(str(exc), encoding="utf-8")
            ledger.append(
                "FAIL", component, status="FALLO_EJECUCION", run_id=run_id, parent_run_id=workflow_run_id,
                metadata_control={"origin": "guardia", "input_sha256": input_hash, "motivo": type(exc).__name__, "reason": str(exc)},
                facets={"error_details": {"type": type(exc).__name__, "message": str(exc)}},
            )
            previous_failure = component
            stopped = strict

    report = evaluar(config, ledger_file, base)
    report["run_id"] = workflow_run_id
    report["strict_mode"] = strict
    report["strict_mode_env_var"] = strict_env
    report["changed_files"] = changed
    report["ledger_path"] = str(ledger_file.relative_to(base)) if ledger_file.is_relative_to(base) else str(ledger_file)
    report["contornos"] = {
        component: siguiente_contorno(str(value["motivo"]))
        for component, value in report["estados"].items()
        if value["estado"] == "FALLO_EJECUCION"
    }
    if not strict:
        report["gate_disabled_reason"] = f"{strict_env}=0"
        exit_code = 0
    else:
        exit_code = int(config["gatekeeper"].get("exit_code_on_fail", 9)) if report["failed"] else 0
    report["exit_code"] = exit_code
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    return report, exit_code
