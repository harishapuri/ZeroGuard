"""ZeroGuard plane stories through the unified orchestrator."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from zeroguard.bootstrap import UNIFIED_ROOT  # noqa: E402
from framework.orchestrator import Orchestrator  # noqa: E402

EX = UNIFIED_ROOT / "examples"
FAIL = EX / "checkov_fail.json"
PASS = EX / "checkov_pass.json"
OK = EX / "telemetry_ok.json"


def _run(checkov: Path, telemetry: Path) -> dict:
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    tmp.close()
    return Orchestrator(Path(tmp.name)).run(checkov, telemetry, service="zg-test")


class TrustPlane(unittest.TestCase):
    def test_fail_has_weak_pillars_and_blocks(self) -> None:
        result = _run(FAIL, OK)
        zg = result["zeroguard"]
        self.assertIn("pillars", zg)
        self.assertEqual(len(zg["pillars"]), 7)
        self.assertGreater(zg["gamma"], 0.0)
        self.assertLess(zg["psi"], result["crc"]["eta"])
        self.assertEqual(result["governance"]["decision"]["dsa"], "BLOCK")

    def test_pass_has_high_psi(self) -> None:
        result = _run(PASS, OK)
        self.assertGreater(result["zeroguard"]["psi"], 0.5)
        self.assertEqual(result["zeroguard"]["sigma"], "ok")
        self.assertEqual(result["governance"]["decision"]["action"], "ALLOW")


class ZeroGuardCli(unittest.TestCase):
    def test_focus_prints_trust(self) -> None:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "zeroguard",
                str(FAIL),
                "--telemetry",
                str(OK),
                "--focus",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["plane"], "zeroguard")
        self.assertIn("psi", payload["zeroguard"])
        self.assertIn("pillars", payload["zeroguard"])
