"""Clone a git repo and run Checkov. The gate still reads Checkov JSON only.

Fill `examples/scan_target.placeholder.json` (git_url) then:

    python3 -m cicd --scan scan_target.placeholder.json
    python3 -m framework.cli --scan examples/scan_target.placeholder.json
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

PLACEHOLDER_MARKERS = (
    "REPLACE_WITH_GIT_REPO_URL",
    "YOUR_GIT_REPO_URL",
    "https://github.com/ORG/REPO.git",
)


class ScanTargetError(ValueError):
    pass


def is_filled_git_url(git_url: str | None) -> bool:
    url = str(git_url or "").strip()
    return bool(url) and url not in PLACEHOLDER_MARKERS


def parse_scan_target(raw: dict[str, Any], *, source: str = "") -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ScanTargetError("scan target must be a JSON object")
    git_url = str(raw.get("git_url") or raw.get("repo") or "").strip()
    if not is_filled_git_url(git_url):
        raise ScanTargetError(
            "Fill git_url in the scan placeholder (clone URL or local path). "
            "Leave the other fields as-is until you need them."
        )
    ref = str(raw.get("ref") or raw.get("branch") or "").strip()
    rel = str(raw.get("path") or raw.get("scan_path") or ".").strip() or "."
    telemetry = raw.get("telemetry")
    telemetry_path = Path(telemetry) if telemetry else None
    return {
        "git_url": git_url,
        "ref": ref or None,
        "path": rel,
        "telemetry": telemetry_path,
        "source": source,
    }


def load_scan_target(path: Path | str) -> dict[str, Any]:
    raw = json.loads(Path(path).read_text())
    return parse_scan_target(raw, source=str(path))


def _clone(git_url: str, dest: Path, ref: str | None) -> None:
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    cmd = ["git", "clone", "--depth", "1"]
    if ref:
        cmd.extend(["--branch", ref])
    cmd.extend([git_url, str(dest)])
    subprocess.run(cmd, check=True, env=env, capture_output=True, text=True)


def _run_checkov(scan_root: Path, out_json: Path) -> None:
    bundled = scan_root / "checkov.json"
    checkov = shutil.which("checkov")
    if checkov:
        proc = subprocess.run(
            [checkov, "-d", str(scan_root), "-o", "json"],
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.stdout.strip():
            out_json.write_text(proc.stdout)
            return
        if bundled.is_file():
            shutil.copyfile(bundled, out_json)
            return
        raise ScanTargetError(proc.stderr.strip() or "checkov produced no JSON")
    if bundled.is_file():
        shutil.copyfile(bundled, out_json)
        return
    raise ScanTargetError(
        "checkov is not on PATH. Install it (`pip install checkov`) "
        "or put a Checkov JSON file named checkov.json in the repo you scan."
    )


def clone_and_scan(
    target: dict[str, Any],
    *,
    work_dir: Path | None = None,
) -> tuple[Path, Path | None]:
    """Clone git_url, run Checkov on `path`, return (checkov_json, telemetry)."""
    root = Path(work_dir) if work_dir else Path(tempfile.mkdtemp(prefix="crc-scan-"))
    root.mkdir(parents=True, exist_ok=True)
    dest = root / "repo"
    if dest.exists():
        shutil.rmtree(dest)
    try:
        _clone(target["git_url"], dest, target.get("ref"))
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or exc.stdout or str(exc)).strip()
        raise ScanTargetError(f"git clone failed: {err}") from exc
    scan_root = (dest / target["path"]).resolve()
    if not str(scan_root).startswith(str(dest.resolve())):
        raise ScanTargetError("scan path must stay inside the cloned repo")
    if not scan_root.exists():
        raise ScanTargetError(f"scan path not found in repo: {target['path']}")
    out_json = root / "checkov.json"
    _run_checkov(scan_root, out_json)
    telemetry = target.get("telemetry")
    if telemetry and not Path(telemetry).is_file():
        alt = dest / str(telemetry)
        telemetry = alt if alt.is_file() else None
    return out_json, telemetry
