"""Demo stories and expected gate picks for the ZeroGuard plane."""

from __future__ import annotations

from pathlib import Path

from zeroguard.bootstrap import ROOT, UNIFIED_ROOT

EXAMPLES = UNIFIED_ROOT / "examples"
STATIC = ROOT / "demo" / "static"
DEMO_AUDIT = ROOT / "data" / "demo_audit.jsonl"
PORT = 8873
HOST = "127.0.0.1"
SITE = f"http://{HOST}:{PORT}"
TITLE = "ZeroGuard — trust demo"
KICKER = "ZeroGuard · trust plane"

STORIES: dict[str, tuple[Path, Path, str, str]] = {
    "pass": (
        EXAMPLES / "checkov_pass.json",
        EXAMPLES / "telemetry_ok.json",
        "chatbot-api",
        "Pillars look locked down. If rules and stay-up agree, go.",
    ),
    "fail": (
        EXAMPLES / "checkov_fail.json",
        EXAMPLES / "telemetry_hot.json",
        "chatbot-api",
        "Open door, public bucket, wildcard IAM, and hot traffic. Stop.",
    ),
    "secure_but_hot": (
        EXAMPLES / "checkov_pass.json",
        EXAMPLES / "telemetry_hot.json",
        "chatbot-api",
        "Trust is fine. Stay-up still rolls back on hot φ_1h — fusion, not one report.",
    ),
    "open_sg_but_calm": (
        EXAMPLES / "checkov_fail.json",
        EXAMPLES / "telemetry_ok.json",
        "chatbot-api",
        "Calm traffic, but P2/P6 are open. ZeroGuard residual still blocks.",
    ),
    "warn_rising_errors": (
        EXAMPLES / "checkov_pass.json",
        EXAMPLES / "telemetry_warn_phi6.json",
        "chatbot-api",
        "Trust is green. Rising errors still say wait.",
    ),
    "warn_capacity": (
        EXAMPLES / "checkov_pass.json",
        EXAMPLES / "telemetry_warn_kappa.json",
        "chatbot-api",
        "Trust is green. Capacity deficit still says wait.",
    ),
    "rollback": (
        EXAMPLES / "checkov_pass.json",
        EXAMPLES / "telemetry_rollback.json",
        "chatbot-api",
        "Trust is green, but the live site is down. Undo.",
    ),
}

STORY_ORDER = [
    "pass",
    "warn_capacity",
    "warn_rising_errors",
    "fail",
    "secure_but_hot",
    "open_sg_but_calm",
    "rollback",
]

EXPECTED = {
    "pass": ("PASS", "ALLOW"),
    "fail": ("BLOCK", "BLOCK_DEPLOYMENT"),
    "secure_but_hot": ("BLOCK", "ROLLBACK"),
    "open_sg_but_calm": ("BLOCK", "BLOCK_DEPLOYMENT"),
    "warn_rising_errors": ("WARN", "WARN"),
    "warn_capacity": ("WARN", "WARN"),
    "rollback": ("BLOCK", "ROLLBACK"),
}
