# Generic execution guard

This package validates execution, evidence and declared component flow. It is independent of the application that uses it and imports only the Python standard library.

## Event ledger

The ledger is append-only JSONL. Each event contains:

- `run_id`: unique identifier for this execution.
- `parent_run_id`: parent execution, when nested.
- `timestamp`: UTC ISO-8601 timestamp.
- `component`: stable component identifier from the project configuration.
- `event`: `START`, `COMPLETE` or `FAIL`.
- `metadata_control`: the only section used for gate decisions. It carries status, stage, origin, input/output SHA-256, artifact hash, evidence, reason and declared consumers.
- `facets`: execution identity and structured error details, compatible with lineage-style event facets.
- `payload_negocio`: application-owned payload. The guard never reads it to decide status.

A component is not accepted merely because an event says it ran. A successful completion needs an evidence reference and an output hash; components that require input also need an input hash. Declared artifacts must exist, be non-empty, remain inside the repository when that security rule is enabled, and contain the configured keys when JSON keys are required.

Python components can use `componente()` as a context manager or `@pieza()` as a decorator. Nested calls inherit a parent run identifier through `contextvars`. External commands are executed by the configuration runner and receive the same ledger treatment.

## Five states

| State | Meaning | Gate |
|---|---|---|
| `OK_CON_EVIDENCIA` | Execution and required evidence are observed and valid. | Pass |
| `INFO_CORRIO_SIN_SENAL` | The component ran, but produced no usable signal for this case. | Informational |
| `INFO_OMISION_CONTRACTUAL` | The component was omitted by an explicit condition or declared optional contract. | Informational |
| `FALLO_EJECUCION` | Execution failed, evidence is missing, a required component was not invoked, or a declared output has no consumer. | Fail |
| `REQUIERE_CONTRATO` | The observed state or component contract is not defined. | Report; does not fail the gate |

The following markers are failures, not successful execution: `SIMULADO_FIXTURE`, `API_PENDING`, `APAGADA_POR_FLAG`, `NO_INVOCADO`, `OMITIDO_SIN_CONTRATO` and `REPORTED_EXECUTED_NOT_OBSERVED`.

A persisted output from a non-terminal component that declares downstream consumers but reaches none is `FALLO_EJECUCION` with reason `OUTPUT_PERSISTED_WITHOUT_CONSUMER`. A terminal component does not require a consumer.

## Configuration

Every consuming project owns a `guardia.config.json` file. It declares:

- `security.allowed_packages`: permitted dependency distributions listed in requirements files.
- `security.fail_on_outside_artifact`: reject evidence paths outside the repository root.
- `gatekeeper.exit_code_on_fail`: defaults to 9.
- `gatekeeper.strict_mode_env_var`: defaults to `GUARDIA_ESTRICTA`; strict mode is on unless the variable is explicitly `0`.
- `gatekeeper.exclude_sidecars`: patterns excluded from artifact discovery.
- `topology.expected_components`: required/optional components, terminal status, feeds, consumed components, input requirements, conditions, command or built-in action, evidence and expected artifacts/keys.

When strict mode is disabled, the run still records the override in the ledger and reports failures; only the process exit gate is disabled. Only the CLI returns the configured failure exit code.

## Built-in checks

- `compile_changed_python`: compile changed Python files only.
- `placeholder_scan`: reject placeholder markers in changed Python files.
- `size_delta`: reject a changed Python file that is more than 20% smaller than its previous revision.
- `package_policy`: enforce the dependency allowlist against declared requirements files.
- `tests`: run pytest when installed, otherwise unittest discovery. A project can declare `test_paths` to restrict execution to its approved test contract set.
- `smokes`: execute discovered shell and Python smoke scripts.

The runner stops after the first failure in strict mode and records downstream required components as `NO_INVOCADO`. It never converts a failed or unknown state into success.

## Contorno

After a failure, `siguiente_contorno()` treats the obstacle as a stone and proposes a different water route (integrity, path, dependency, permission, contract or unknown). It allows at most three distinct routes before escalation. It does not mark a component as successful and does not close an order.

## Minimal use

```python
from guardia import Ledger, componente, configurar_ledger, pieza

ledger = configurar_ledger(".guardia/ledger.jsonl", root=".")

with componente("source", ledger, input_paths=["input.json"], output_paths=["output.json"], evidence="run://source"):
    create_output()

@pieza("validator")
def validate():
    return True
```

Run the project gate with:

```bash
python -m guardia.cli --config guardia.config.json --ledger .guardia/ledger.jsonl --report .guardia/report.json
```
