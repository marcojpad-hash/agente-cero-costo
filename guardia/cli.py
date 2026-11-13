"""Command-line entry point for the generic execution guard."""

from __future__ import annotations

import argparse
import json
import sys

from .core import ejecutar_configuracion


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate component execution and evidence.")
    parser.add_argument("--config", default="guardia.config.json")
    parser.add_argument("--ledger", default=".guardia/ledger.jsonl")
    parser.add_argument("--report", default=".guardia/report.json")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    try:
        report, code = ejecutar_configuracion(args.config, args.ledger, args.report, args.root)
    except Exception as exc:
        print(json.dumps({
            "failed": True,
            "state": "FALLO_EJECUCION",
            "error": f"{type(exc).__name__}: {exc}",
            "exit_code": 9,
        }, ensure_ascii=False), file=sys.stderr)
        return 9
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
