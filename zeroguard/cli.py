"""ZeroGuard CLI: Checkov → NIST pillars / Ξ / Γ / Ψ, fused with CRC and InfraAgent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from zeroguard.bootstrap import UNIFIED_ROOT  # noqa: F401

from framework.orchestrator import Orchestrator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="ZeroGuard plane: IaC + telemetry → unified trust gate."
    )
    parser.add_argument("checkov_json", type=Path)
    parser.add_argument("--telemetry", type=Path, default=None)
    parser.add_argument("--service", default="zeroguard")
    parser.add_argument("--autonomy", type=int, default=2, choices=(0, 1, 2, 3))
    parser.add_argument("--enforce", action="store_true")
    parser.add_argument("--audit", type=Path, default=None)
    parser.add_argument("--focus", action="store_true")
    args = parser.parse_args(argv)

    result = Orchestrator(args.audit).run(
        args.checkov_json,
        args.telemetry,
        autonomy=args.autonomy,
        shadow=not args.enforce,
        service=args.service,
    )
    if args.focus:
        payload = {
            "plane": "zeroguard",
            "zeroguard": result["zeroguard"],
            "decision": result["governance"]["decision"],
            "shadow": result["governance"]["shadow"],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(result, indent=2))
    if args.enforce and result["governance"]["decision"]["dsa"] == "BLOCK":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
