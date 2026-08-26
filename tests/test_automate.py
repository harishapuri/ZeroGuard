"""Headless demo automation must match the expected fused picks."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class AutomateStories(unittest.TestCase):
    def test_all_stories_match_expected(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "zeroguard.automate"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["passed"])
        self.assertEqual(len(payload["stories"]), 7)
        self.assertEqual(payload["stories"][5]["action"], "BLOCK_DEPLOYMENT")
