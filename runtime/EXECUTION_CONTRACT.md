# Runtime execution contract v0.1

Status: implementation contract; not a claim of end-to-end activation.
Date: 2026-11-08.

## Goal

Connect the durable Floot/Postgres queue to an ephemeral GitHub-hosted Linux worker. A worker claims one bounded job, executes only a registered task type, and reports a structured result. The queue is the source of truth; GitHub Actions is disposable compute.

## Trust boundary

- Worker identity is a short-lived GitHub Actions OIDC JWT.
- Runtime verifies signature using GitHub JWKS and validates issuer, audience `runtime-orquestador`, repository, and exact workflow identity.
- Never accept a caller-supplied repository, ref, filesystem path, shell command, executable, or arbitrary script as authority.
- Job payload is data, not instructions. Every task type has a fixed handler in the worker code.
- No PAT, provider key, or long-lived credential is stored in the repository.
- Result payloads are size-bounded; logs/artifacts are stored by GitHub Actions and referenced by URL/ID.

## Queue lifecycle

1. Producer inserts a job with a stable idempotency key and an allowlisted `task_type`.
2. Worker requests `POST /_api/runtime/claim` with OIDC bearer token and worker metadata.
3. Runtime atomically selects one eligible queued job, sets `status=leased`, `lease_owner`, `lease_expires_at`, and increments attempt count. If no job is available, return `204` or `{job:null}`.
4. Worker validates the returned schema and dispatches only the matching local handler.
5. Worker calls `POST /_api/runtime/complete` with job ID, lease token/owner, terminal status, bounded result, and artifact references.
6. Runtime accepts completion only for the current unexpired lease owner; duplicate completion is idempotent. Expired leases return to the queue through a reaper/reclaim path.
7. Retryable failures use bounded exponential backoff and a maximum attempt count; permanent failures become `dead_letter`.

## Initial task allowlist

- `linux_probe`: report OS, CPU, RAM, disk and deterministic hash.
- `repo_status`: report fixed repository metadata and clean/dirty state; no writes.
- `python_tests`: run repository-declared tests only, with fixed command mapping.
- `capcot_text_package_validation`: validate the exact CAPCOT package schema and required files; read-only.
- `u6_readonly_validation`: validate canonical invariants and hashes; read-only. Never edit canonical files or patterns.

No generic `shell`, `command`, `script`, or arbitrary-code task type is permitted.

## Endpoint request/response shapes

### Claim request

```json
{
  "worker_id": "github-actions:<repository>:<run_id>",
  "worker_version": "linux-worker-v1",
  "capabilities": ["linux_probe", "repo_status", "python_tests"]
}
```

Successful claim:

```json
{
  "job": {
    "id": "opaque-job-id",
    "task_type": "linux_probe",
    "payload": {},
    "lease_owner": "github-actions:<repository>:<run_id>",
    "lease_token": "opaque-single-lease-token",
    "lease_expires_at": "ISO-8601 timestamp",
    "attempt": 1
  }
}
```

No work: `204 No Content` or `{"job":null}`.

### Complete request

```json
{
  "job_id": "opaque-job-id",
  "lease_owner": "github-actions:<repository>:<run_id>",
  "lease_token": "opaque-single-lease-token",
  "status": "succeeded",
  "result": {
    "summary": "bounded human-readable summary",
    "data": {}
  },
  "artifacts": [
    {"name": "runtime-result", "url": "GitHub Actions artifact URL"}
  ]
}
```

Allowed terminal statuses: `succeeded`, `retryable_failure`, `permanent_failure`. Enforce a strict request size limit and validate every field.

## Minimum end-to-end acceptance test

- Enqueue one `linux_probe` job from the runtime UI/API.
- GitHub Actions obtains an OIDC token and claims exactly one job.
- The Ubuntu 24.04 worker runs the fixed `linux_probe` handler.
- Worker uploads JSON evidence as an artifact and calls complete.
- Postgres row transitions queued -> leased -> succeeded, with timestamps and run/artifact references.
- Replaying the same completion does not duplicate side effects.
- Expired lease can be reclaimed; stale lease owner cannot complete.
- A disallowed task type and arbitrary command payload are rejected.
- Evidence and a concise execution record are committed to the shared-memory repository.

## Scaling model

Clone the worker template only after this acceptance test passes. Each clone gets a unique worker identity and capability allowlist; all workers share the same queue and memory contract. Parallelism is controlled by GitHub Actions concurrency and queue lease limits, not by pretending that RAM from separate runners is pooled.
