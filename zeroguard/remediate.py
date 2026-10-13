"""Opt-in remediation for a small allowlist of low-risk Terraform settings.

Default is a dry run: print the plan and a unified diff, touch nothing.
`--apply` writes the change to the .tf files under `--root`.

Scope is deliberately narrow:

* Only Checkov IDs on ALLOWLIST are fixed. Each one sets a single top-level
  boolean on one resource type and does not replace or destroy the resource.
* IAM, security groups, network ACLs and anything else outside the
  allowlist are always skipped, with a reason. ZeroGuard still never
  auto-applies IAM or network changes.
* Every run (dry or applied) can append a row to the SHA-256 audit chain
  (`--audit`), so the fix is reviewable next to the gate decision.

Usage:
    python3 -m zeroguard.remediate CHECKOV_JSON --root DIR            # dry run
    python3 -m zeroguard.remediate CHECKOV_JSON --root DIR --apply    # write
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from zeroguard.bootstrap import UNIFIED_ROOT  # noqa: F401

from framework.audit import AuditChain


@dataclass(frozen=True)
class Fix:
    resource_types: tuple[str, ...]
    attribute: str
    value: str
    why: str


ALLOWLIST: dict[str, Fix] = {
    "CKV_AWS_7": Fix(("aws_kms_key",), "enable_key_rotation", "true",
                     "Annual KMS key rotation; no resource replacement."),
    "CKV_AWS_27": Fix(("aws_sqs_queue",), "sqs_managed_sse_enabled", "true",
                      "SQS-managed encryption at rest; in-place update."),
    "CKV_AWS_36": Fix(("aws_cloudtrail",), "enable_log_file_validation", "true",
                      "CloudTrail digest validation; in-place update."),
    "CKV_AWS_131": Fix(("aws_lb", "aws_alb"), "drop_invalid_header_fields", "true",
                       "ALB drops malformed headers; in-place update."),
    "CKV_AWS_150": Fix(("aws_lb", "aws_alb"), "enable_deletion_protection", "true",
                       "Load balancer deletion protection; in-place update."),
    "CKV_AWS_293": Fix(("aws_db_instance",), "deletion_protection", "true",
                       "RDS deletion protection; in-place update."),
}

# Never touched, even if someone adds an allowlist entry by mistake.
DENY_PREFIXES = (
    "aws_iam_",
    "aws_security_group",
    "aws_vpc_security_group",
    "aws_network_acl",
    "aws_default_security_group",
    "aws_default_network_acl",
)

MAX_FIXES_DEFAULT = 10


def load_failed_checks(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text())
    reports = data if isinstance(data, list) else [data]
    out: list[dict[str, Any]] = []
    for report in reports:
        out.extend(report.get("results", {}).get("failed_checks", []))
    return out


def _strip_line_comment(line: str) -> str:
    out, in_str, i = [], False, 0
    while i < len(line):
        ch = line[i]
        if ch == '"' and (i == 0 or line[i - 1] != "\\"):
            in_str = not in_str
        if not in_str and (ch == "#" or line.startswith("//", i)):
            break
        out.append(ch)
        i += 1
    return "".join(out)


def find_block(lines: list[str], rtype: str, name: str) -> tuple[int, int] | None:
    """Return (open_line, close_line) indexes of `resource "rtype" "name" {`."""
    head = re.compile(r'^\s*resource\s+"%s"\s+"%s"\s*\{' % (re.escape(rtype), re.escape(name)))
    for start, line in enumerate(lines):
        if not head.match(line):
            continue
        depth = 0
        for idx in range(start, len(lines)):
            code = _strip_line_comment(lines[idx])
            code = re.sub(r'"(?:\\.|[^"\\])*"', '""', code)
            depth += code.count("{") - code.count("}")
            if depth == 0:
                return start, idx
        return None
    return None


def _top_level_attr(lines: list[str], start: int, end: int, attr: str) -> int | None:
    pattern = re.compile(r"^\s*%s\s*=" % re.escape(attr))
    depth = 0
    for idx in range(start, end + 1):
        code = re.sub(r'"(?:\\.|[^"\\])*"', '""', _strip_line_comment(lines[idx]))
        if depth == 1 and pattern.match(lines[idx]):
            return idx
        depth += code.count("{") - code.count("}")
    return None


def _indent_for(lines: list[str], start: int, end: int) -> str:
    for idx in range(start + 1, end):
        stripped = lines[idx].strip()
        if stripped and not stripped.startswith(("#", "//")):
            return lines[idx][: len(lines[idx]) - len(lines[idx].lstrip())]
    return "  "


def _safe_file(root: Path, file_path: str) -> Path | None:
    candidate = (root / file_path.lstrip("/")).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def plan(checks: list[dict[str, Any]], root: Path, max_fixes: int = MAX_FIXES_DEFAULT
         ) -> tuple[list[dict[str, Any]], dict[Path, tuple[str, str]]]:
    """Build the fix plan and the new text for each touched file (nothing is written)."""
    rows: list[dict[str, Any]] = []
    texts: dict[Path, list[str]] = {}
    originals: dict[Path, str] = {}
    applied = 0
    for check in checks:
        cid = check.get("check_id", "")
        resource = check.get("resource", "")
        row = {"check_id": cid, "resource": resource, "file": check.get("file_path", "")}
        rtype, _, name = resource.partition(".")
        fix = ALLOWLIST.get(cid)
        if rtype.startswith(DENY_PREFIXES):
            rows.append({**row, "action": "skip", "reason": "IAM / network resource: never auto-applied"})
            continue
        if fix is None:
            rows.append({**row, "action": "skip", "reason": "check not on the low-risk allowlist"})
            continue
        if rtype not in fix.resource_types or not name:
            rows.append({**row, "action": "skip", "reason": "resource type does not match the allowlisted fix"})
            continue
        if applied >= max_fixes:
            rows.append({**row, "action": "skip", "reason": f"max {max_fixes} fixes per run"})
            continue
        path = _safe_file(root, row["file"])
        if path is None:
            rows.append({**row, "action": "skip", "reason": "file not found under --root"})
            continue
        if path not in texts:
            originals[path] = path.read_text()
            texts[path] = originals[path].splitlines(keepends=True)
        lines = texts[path]
        block = find_block(lines, rtype, name)
        if block is None:
            rows.append({**row, "action": "skip", "reason": "resource block not found"})
            continue
        start, end = block
        wanted = f"{fix.attribute} = {fix.value}"
        at = _top_level_attr(lines, start, end, fix.attribute)
        if at is not None:
            current = lines[at].split("=", 1)[1].strip()
            current = _strip_line_comment(current).strip()
            if current == fix.value:
                rows.append({**row, "action": "none", "reason": "already set"})
                continue
            if current.endswith(("[", "{", "(", "<<")) or current.startswith("<<"):
                rows.append({**row, "action": "skip", "reason": "multi-line value; edit by hand"})
                continue
            indent = lines[at][: len(lines[at]) - len(lines[at].lstrip())]
            newline = "\n" if lines[at].endswith("\n") else ""
            lines[at] = f"{indent}{wanted}{newline}"
            action = "replace"
        else:
            indent = _indent_for(lines, start, end)
            lines.insert(end, f"{indent}{wanted}\n")
            action = "insert"
        applied += 1
        rows.append({**row, "action": action, "change": wanted, "why": fix.why})
    changed = {
        p: (originals[p], "".join(texts[p]))
        for p in texts
        if "".join(texts[p]) != originals[p]
    }
    return rows, changed


def unified_diff(changed: dict[Path, tuple[str, str]], root: Path) -> str:
    chunks = []
    for path, (old, new) in sorted(changed.items()):
        rel = path.resolve().relative_to(root.resolve())
        chunks.extend(difflib.unified_diff(
            old.splitlines(keepends=True), new.splitlines(keepends=True),
            fromfile=f"a/{rel}", tofile=f"b/{rel}",
        ))
    return "".join(chunks)


def run(checkov_json: Path, root: Path, apply: bool = False, audit: Path | None = None,
        max_fixes: int = MAX_FIXES_DEFAULT) -> dict[str, Any]:
    rows, changed = plan(load_failed_checks(checkov_json), root, max_fixes)
    diff = unified_diff(changed, root)
    if apply:
        for path, (_, new) in changed.items():
            path.write_text(new)
    fixed = [r for r in rows if r["action"] in ("insert", "replace")]
    result = {
        "mode": "apply" if apply else "dry_run",
        "apply": apply,
        "fixed": len(fixed),
        "skipped": sum(1 for r in rows if r["action"] == "skip"),
        "files": sorted(str(p.resolve().relative_to(root.resolve())) for p in changed),
        "plan": rows,
        "diff": diff,
    }
    if audit is not None:
        entry = AuditChain(audit).append(
            "Remediation",
            {"checkov": str(checkov_json), "fixes": [f"{r['check_id']}:{r['resource']}" for r in fixed]},
            "apply" if apply else "dry_run",
            "written" if apply and fixed else "no_write",
            {"files": result["files"], "skipped": result["skipped"]},
        )
        result["audit_hash"] = entry["hash"]
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Opt-in fixes for allowlisted low-risk Terraform settings (dry run by default)."
    )
    parser.add_argument("checkov_json", type=Path)
    parser.add_argument("--root", type=Path, required=True, help="Directory that Checkov scanned")
    parser.add_argument("--apply", action="store_true", help="Write the changes (default: dry run)")
    parser.add_argument("--audit", type=Path, default=None, help="Append a row to this audit chain")
    parser.add_argument("--max-fixes", type=int, default=MAX_FIXES_DEFAULT)
    parser.add_argument("--json", action="store_true", help="Print the full JSON result")
    args = parser.parse_args(argv)

    result = run(args.checkov_json, args.root, args.apply, args.audit, args.max_fixes)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for row in result["plan"]:
            detail = row.get("change") or row.get("reason", "")
            print(f"{row['action']:<8} {row['check_id']:<12} {row['resource']:<40} {detail}")
        if result["diff"]:
            print()
            print(result["diff"], end="")
        verb = "Applied" if args.apply else "Dry run:"
        print(f"\n{verb} {result['fixed']} fix(es), {result['skipped']} skipped."
              + ("" if args.apply else " Re-run with --apply to write."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
