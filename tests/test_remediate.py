"""Opt-in remediation: dry run by default, allowlist only, never IAM or network."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from zeroguard import remediate  # noqa: E402
from framework.audit import AuditChain  # noqa: E402

EXAMPLE = ROOT / "examples" / "remediate"
CHECKOV = EXAMPLE / "checkov_remediate.json"


class Remediate(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        shutil.copytree(EXAMPLE / "infra", self.tmp / "infra")
        self.before = {p.name: p.read_text() for p in (self.tmp / "infra").glob("*.tf")}

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def _text(self, name: str) -> str:
        return (self.tmp / "infra" / name).read_text()

    def test_dry_run_writes_nothing(self) -> None:
        result = remediate.run(CHECKOV, self.tmp)
        self.assertEqual(result["mode"], "dry_run")
        self.assertFalse(result["apply"])
        self.assertEqual(result["fixed"], 5)
        self.assertIn("+  enable_key_rotation = true", result["diff"])
        for name, text in self.before.items():
            self.assertEqual(self._text(name), text)

    def test_apply_writes_allowlisted_fixes(self) -> None:
        result = remediate.run(CHECKOV, self.tmp, apply=True)
        self.assertEqual(result["fixed"], 5)
        data = self._text("data.tf")
        self.assertIn("enable_key_rotation = true", data)
        self.assertIn("sqs_managed_sse_enabled = true", data)
        self.assertIn("deletion_protection = true", data)
        self.assertNotIn("deletion_protection = false", data)
        edge = self._text("edge.tf")
        self.assertIn("enable_deletion_protection = true", edge)
        self.assertIn("drop_invalid_header_fields = true", edge)

    def test_never_touches_iam_or_security_groups(self) -> None:
        result = remediate.run(CHECKOV, self.tmp, apply=True)
        by_id = {r["check_id"]: r for r in result["plan"]}
        self.assertEqual(by_id["CKV_AWS_24"]["action"], "skip")
        self.assertEqual(by_id["CKV_AWS_40"]["action"], "skip")
        edge = self._text("edge.tf")
        self.assertIn('cidr_blocks = ["0.0.0.0/0"]', edge)
        self.assertIn('Action = "*"', edge)

    def test_deny_list_wins_over_allowlist(self) -> None:
        original = remediate.ALLOWLIST.copy()
        try:
            remediate.ALLOWLIST["CKV_AWS_24"] = remediate.Fix(
                ("aws_security_group",), "description", "\"x\"", "should never run")
            result = remediate.run(CHECKOV, self.tmp, apply=True)
            row = next(r for r in result["plan"] if r["check_id"] == "CKV_AWS_24")
            self.assertEqual(row["action"], "skip")
        finally:
            remediate.ALLOWLIST.clear()
            remediate.ALLOWLIST.update(original)

    def test_unknown_check_is_skipped(self) -> None:
        result = remediate.run(CHECKOV, self.tmp)
        row = next(r for r in result["plan"] if r["check_id"] == "CKV_AWS_144")
        self.assertEqual(row["action"], "skip")

    def test_second_apply_is_a_no_op(self) -> None:
        remediate.run(CHECKOV, self.tmp, apply=True)
        snapshot = {p.name: p.read_text() for p in (self.tmp / "infra").glob("*.tf")}
        result = remediate.run(CHECKOV, self.tmp, apply=True)
        self.assertEqual(result["fixed"], 0)
        self.assertEqual(result["diff"], "")
        for name, text in snapshot.items():
            self.assertEqual(self._text(name), text)

    def test_max_fixes_caps_a_run(self) -> None:
        result = remediate.run(CHECKOV, self.tmp, apply=True, max_fixes=2)
        self.assertEqual(result["fixed"], 2)

    def test_path_outside_root_is_refused(self) -> None:
        bad = self.tmp / "bad.json"
        bad.write_text(json.dumps({"results": {"failed_checks": [{
            "check_id": "CKV_AWS_7", "resource": "aws_kms_key.ledger",
            "file_path": "/../../etc/passwd"}]}}))
        result = remediate.run(bad, self.tmp, apply=True)
        self.assertEqual(result["plan"][0]["action"], "skip")
        self.assertEqual(result["fixed"], 0)

    def test_audit_chain_records_the_run(self) -> None:
        audit = self.tmp / "audit.jsonl"
        result = remediate.run(CHECKOV, self.tmp, apply=True, audit=audit)
        chain = AuditChain(audit)
        self.assertTrue(chain.verify())
        last = chain.entries[-1]
        self.assertEqual(last["event"], "Remediation")
        self.assertEqual(last["action"], "apply")
        self.assertEqual(last["hash"], result["audit_hash"])
        self.assertEqual(len(last["traces"]["fixes"]), 5)

    def test_cli_defaults_to_dry_run(self) -> None:
        code = remediate.main([str(CHECKOV), "--root", str(self.tmp), "--json"])
        self.assertEqual(code, 0)
        for name, text in self.before.items():
            self.assertEqual(self._text(name), text)


if __name__ == "__main__":
    unittest.main()
