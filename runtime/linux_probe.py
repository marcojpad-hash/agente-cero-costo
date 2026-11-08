#!/usr/bin/env python3
"""Deterministic Linux runner probe; no secrets, network calls, or arbitrary commands."""
from __future__ import annotations
import hashlib, json, os, platform, shutil, sys
from datetime import datetime, timezone
from pathlib import Path

def meminfo():
    values = {}
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            key, raw = line.split(":", 1)
            parts = raw.strip().split()
            if parts and parts[0].isdigit():
                values[key] = int(parts[0]) * (1024 if len(parts) > 1 and parts[1] == "kB" else 1)
    except Exception as exc:
        values["read_error"] = str(exc)
    return values

def deterministic_payload(seed: str) -> dict:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return {"seed": seed, "sha256": digest, "bytes": len(seed.encode("utf-8"))}

def main():
    seed = "runtime-linux-smoke-v1"
    first, second = deterministic_payload(seed), deterministic_payload(seed)
    if first != second:
        raise SystemExit("repeatability check failed")
    usage = shutil.disk_usage(".")
    memory = meminfo()
    result = {
        "status": "PASS",
        "probe": "runtime-linux-smoke-v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "host": platform.node(),
        "os": platform.platform(),
        "python": sys.version,
        "cpu_count": os.cpu_count(),
        "memory_bytes": {
            "total": memory.get("MemTotal"),
            "available": memory.get("MemAvailable"),
            "free": memory.get("MemFree"),
        },
        "disk_bytes": {"total": usage.total, "free": usage.free},
        "repeatability": {"pass": first == second, "sha256": first["sha256"]},
    }
    Path("runtime-result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not result["memory_bytes"]["total"] or not result["cpu_count"]:
        raise SystemExit("resource measurement incomplete")

if __name__ == "__main__":
    main()
