"""CORS + static files so file:// demo pages can call the local HTTP gate."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Callable

STATIC_FILES = {"styles.css", "app.js", "index.html"}


def apply_cors(handler) -> None:
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "*")


def send_options(handler) -> None:
    handler.send_response(204)
    apply_cors(handler)
    handler.end_headers()


def resolve_static(static_dir: Path, url_path: str) -> Path | None:
    if url_path in {"/", "/index.html"}:
        candidate = static_dir / "index.html"
        return candidate if candidate.is_file() else None
    name = url_path[len("/assets/") :] if url_path.startswith("/assets/") else url_path.lstrip("/")
    if "/" in name or name not in STATIC_FILES:
        return None
    candidate = static_dir / name
    return candidate if candidate.is_file() else None


def read_json_body(handler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        data = json.loads(raw.decode() or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def payload_from_query(qs: dict[str, list[str]]) -> dict[str, str]:
    def first(*keys: str, default: str = "") -> str:
        for key in keys:
            vals = qs.get(key) or []
            if vals and str(vals[0]).strip():
                return str(vals[0]).strip()
        return default

    return {
        "git_url": first("git_url", "repo"),
        "ref": first("ref", "branch", default="main"),
        "path": first("path", "scan_path", default="."),
    }


def git_url_from_payload(payload: dict[str, Any] | None) -> str:
    from framework.ingest.git_scan import is_filled_git_url

    raw = payload or {}
    git_url = str(raw.get("git_url") or raw.get("repo") or "").strip()
    return git_url if is_filled_git_url(git_url) else ""


def scan_repo_and_gate(
    git_url: str,
    *,
    ref: str | None = "main",
    path: str = ".",
    audit: Path,
    service: str = "chatbot-api",
) -> dict[str, Any]:
    """Clone the repo, ingest Checkov JSON, run the fused gate once. Shadow; no apply."""
    from framework.ingest.git_scan import clone_and_scan, parse_scan_target
    from framework.orchestrator import Orchestrator

    target = parse_scan_target(
        {"git_url": git_url, "ref": ref or "main", "path": path or "."},
        source="ui",
    )
    with tempfile.TemporaryDirectory(prefix="crc-scan-") as tmp:
        checkov_json, telemetry = clone_and_scan(target, work_dir=Path(tmp))
        result = Orchestrator(audit).run(checkov_json, telemetry, service=service, shadow=True)
    decision = result["governance"]["decision"]
    return {
        "source": "git_scan",
        "git_url": target["git_url"],
        "ref": target.get("ref"),
        "path": target["path"],
        "decision": decision,
        "dsa": decision["dsa"],
        "action": decision["action"],
        "reasons": decision.get("reasons") or [],
        "crc": result.get("crc"),
        "zeroguard": result.get("zeroguard"),
        "infraagent": result.get("infraagent"),
        "governance": result.get("governance"),
        "service": result.get("service"),
        "shadow": True,
        "apply": False,
    }


def handle_automate(
    payload: dict[str, Any] | None = None,
    *,
    run_fixtures: Callable[[], dict[str, Any]],
    audit: Path | None = None,
    service: str = "chatbot-api",
) -> tuple[int, dict[str, Any]]:
    """Always run the 7 fixture stories. Git clone is POST /api/scan only."""
    _ = payload, audit, service
    body = run_fixtures()
    if "source" not in body:
        body = {**body, "source": "fixtures"}
    return 200, body


def handle_scan(
    payload: dict[str, Any] | None,
    *,
    audit: Path,
    service: str = "chatbot-api",
) -> tuple[int, dict[str, Any]]:
    """Clone git_url, scan the tree, run the fused gate. Empty URL does not clone."""
    from framework.ingest.git_scan import ScanTargetError

    payload = payload or {}
    git_url = git_url_from_payload(payload)
    if not git_url:
        return 400, {
            "error": "Fill the Git repo field first (clone URL or local path).",
            "source": "git_scan",
        }
    try:
        return 200, scan_repo_and_gate(
            git_url,
            ref=str(payload.get("ref") or payload.get("branch") or "main").strip() or "main",
            path=str(payload.get("path") or payload.get("scan_path") or ".").strip() or ".",
            audit=audit,
            service=service,
        )
    except ScanTargetError as exc:
        return 400, {"error": str(exc), "source": "git_scan"}
    except Exception as exc:
        return 400, {"error": str(exc), "source": "git_scan"}
