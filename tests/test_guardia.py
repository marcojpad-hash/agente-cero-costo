from __future__ import annotations

from pathlib import Path
import json
import os
import tempfile
import unittest

from guardia.contorno import siguiente_contorno
from guardia.core import evaluar, ejecutar_configuracion
from guardia.ledger import Ledger, componente


def config_for(*components):
    return {
        "security": {"allowed_packages": [], "fail_on_outside_artifact": True},
        "gatekeeper": {
            "exit_code_on_fail": 9,
            "strict_mode_env_var": "GUARDIA_ESTRICTA",
            "strict_mode_default": True,
            "exclude_sidecars": ["*.log", "*.jsonl"],
        },
        "topology": {"expected_components": {name: spec for name, spec in components}},
    }


def spec(required=True, terminal=True, feeds=None, **extra):
    value = {
        "required": required,
        "terminal": terminal,
        "feeds": feeds or [],
        "consumes": [],
        "requires_input": False,
        "expected_artifacts": [],
        "expected_keys_in_output": {},
    }
    value.update(extra)
    return value


def event(component_id, status="EJECUTADO", event_type="COMPLETE", **metadata):
    control = {
        "status": status,
        "evidence": "run://evidence",
        "input_sha256": "input-hash",
        "output_sha256": "output-hash",
    }
    control.update(metadata)
    return {
        "run_id": component_id + "-run",
        "parent_run_id": "workflow-run",
        "timestamp": "2026-11-13T00:00:00+00:00",
        "component": component_id,
        "event": event_type,
        "metadata_control": control,
        "facets": {},
        "payload_negocio": {"status": "OK"},
    }


class GuardStateTests(unittest.TestCase):
    def test_five_states_are_distinct(self):
        config = config_for(
            ("ok", spec()),
            ("signal", spec()),
            ("omitted", spec(required=False)),
            ("failed", spec()),
            ("unknown", spec()),
        )
        records = [
            event("ok"),
            event("signal", "CORRIO_SIN_SENAL"),
            event("omitted", "NOT_APPLICABLE"),
            event("failed", "API_PENDING"),
            event("unknown", "UNRECOGNIZED_STATE"),
        ]
        report = evaluar(config, records)
        states = {key: value["estado"] for key, value in report["estados"].items()}
        self.assertEqual(states["ok"], "OK_CON_EVIDENCIA")
        self.assertEqual(states["signal"], "INFO_CORRIO_SIN_SENAL")
        self.assertEqual(states["omitted"], "INFO_OMISION_CONTRACTUAL")
        self.assertEqual(states["failed"], "FALLO_EJECUCION")
        self.assertEqual(states["unknown"], "REQUIERE_CONTRATO")
        self.assertTrue(report["failed"])

    def test_payload_is_not_authority(self):
        config = config_for(("source", spec()))
        record = event("source", "SIMULADO_FIXTURE")
        record["payload_negocio"] = {"status": "EJECUTADO", "success": True}
        report = evaluar(config, [record])
        self.assertEqual(report["estados"]["source"]["estado"], "FALLO_EJECUCION")

    def test_required_component_not_invoked_fails(self):
        config = config_for(("required", spec(required=True)))
        report = evaluar(config, [])
        self.assertEqual(report["estados"]["required"]["estado"], "FALLO_EJECUCION")

    def test_output_without_consumer_fails(self):
        config = config_for(
            ("producer", spec(feeds=["consumer"], terminal=False)),
            ("consumer", spec(required=False)),
        )
        report = evaluar(config, [event("producer"), event("consumer", "NOT_APPLICABLE")])
        self.assertEqual(
            report["estados"]["producer"]["motivo"],
            "OUTPUT_PERSISTED_WITHOUT_CONSUMER:consumer",
        )

    def test_terminal_component_needs_no_consumer(self):
        config = config_for(("terminal", spec(terminal=True, feeds=[])))
        report = evaluar(config, [event("terminal")])
        self.assertEqual(report["estados"]["terminal"]["estado"], "OK_CON_EVIDENCIA")

    def test_missing_evidence_is_not_success(self):
        config = config_for(("source", spec()))
        record = event("source")
        record["metadata_control"]["evidence"] = None
        report = evaluar(config, [record])
        self.assertEqual(report["estados"]["source"]["estado"], "FALLO_EJECUCION")

    def test_unknown_component_contract_is_reported_not_gated(self):
        config = config_for(("component", spec()))
        report = evaluar(config, [event("component", "REQUIERE_CONTRATO")])
        self.assertEqual(report["estados"]["component"]["estado"], "REQUIERE_CONTRATO")
        self.assertFalse(report["failed"])


class ContextAndContourTests(unittest.TestCase):
    def test_nested_context_records_parent_run(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = Ledger(root / ".guardia" / "ledger.jsonl", root)
            (root / "parent.txt").write_text("parent", encoding="utf-8")
            (root / "child.txt").write_text("child", encoding="utf-8")
            with componente("parent", ledger, output_paths=["parent.txt"], evidence="run://parent") as parent_id:
                with componente("child", ledger, input_paths=["parent.txt"], output_paths=["child.txt"], evidence="run://child"):
                    pass
            records = ledger.read()
            child_start = next(r for r in records if r["component"] == "child" and r["event"] == "START")
            self.assertEqual(child_start["parent_run_id"], parent_id)

    def test_contour_changes_route_and_escalates_after_three(self):
        first = siguiente_contorno("hash mismatch")
        second = siguiente_contorno("hash mismatch", [first])
        third = siguiente_contorno("hash mismatch", [first, second])
        fourth = siguiente_contorno("hash mismatch", [first, second, third])
        self.assertNotEqual(first["accion"], second["accion"])
        self.assertNotEqual(second["accion"], third["accion"])
        self.assertTrue(fourth["escalar"])
        self.assertFalse(first["marca_ok"])
        self.assertFalse(first["cierra_orden"])
        self.assertEqual(first["tipo_obstaculo"], "piedra")
        self.assertEqual(first["ruta_siguiente"], "agua")


class RunnerTests(unittest.TestCase):
    def _write_config(self, root: Path, command: list[str]) -> Path:
        config = config_for(("command", spec(command=command, when="always")))
        path = root / "guardia.config.json"
        path.write_text(json.dumps(config), encoding="utf-8")
        return path

    def test_runner_success_and_failure_exit_code(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = self._write_config(root, [os.sys.executable, "-c", "print('evidence')"])
            os.environ["GUARDIA_EVIDENCE_URL"] = "https://example.invalid/actions/1"
            try:
                report, code = ejecutar_configuracion(config, ".guardia/ok.jsonl", ".guardia/ok.json", root)
                self.assertEqual(code, 0)
                self.assertEqual(report["estados"]["command"]["estado"], "OK_CON_EVIDENCIA")
                config = self._write_config(root, [os.sys.executable, "-c", "raise SystemExit(4)"])
                report, code = ejecutar_configuracion(config, ".guardia/fail.jsonl", ".guardia/fail.json", root)
                self.assertEqual(code, 9)
                self.assertEqual(report["estados"]["command"]["estado"], "FALLO_EJECUCION")
            finally:
                os.environ.pop("GUARDIA_EVIDENCE_URL", None)

    def test_strict_mode_zero_records_override_and_disables_exit_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = self._write_config(root, [os.sys.executable, "-c", "raise SystemExit(4)"])
            os.environ["GUARDIA_ESTRICTA"] = "0"
            try:
                report, code = ejecutar_configuracion(config, ".guardia/run.jsonl", ".guardia/report.json", root)
                self.assertEqual(code, 0)
                self.assertFalse(report["strict_mode"])
                records = Ledger(root / ".guardia" / "run.jsonl", root).read()
                self.assertTrue(any(r["component"] == "guardia.strict_mode" for r in records))
                self.assertTrue(report["failed"])
            finally:
                os.environ.pop("GUARDIA_ESTRICTA", None)

    def test_guard_checkout_is_not_treated_as_caller_dependency_or_test_suite(self):
        from guardia.core import _requirements, _tests_present, _package_policy
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "_guardia" / "tests").mkdir(parents=True)
            (root / "_guardia" / "requirements-mcp.txt").write_text("mcp>=1.0\n", encoding="utf-8")
            (root / "requirements.txt").write_text("numpy>=1.0\n", encoding="utf-8")
            config = {"security": {"allowed_packages": ["numpy"]}}
            self.assertEqual([p.name for p in _requirements(root)], ["requirements.txt"])
            self.assertFalse(_tests_present(root))
            okay, rejected, _ = _package_policy(root, config)
            self.assertTrue(okay)
            self.assertEqual(rejected, [])

    def test_placeholder_scanner_rejects_marker_in_temporary_source(self):
        from guardia.core import _run_builtin
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "changed.py"
            marker = "PLACE" + "HOLDER"
            source.write_text("# " + marker, encoding="utf-8")
            code, _, error = _run_builtin("placeholder_scan", root, ["changed.py"], {})
            self.assertNotEqual(code, 0)
            self.assertIn("changed.py", error)


if __name__ == "__main__":
    unittest.main()
