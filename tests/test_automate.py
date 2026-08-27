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


def _post_automate(handler_cls, payload: dict) -> tuple[int, dict]:
    import threading
    import urllib.error
    import urllib.request
    from http.server import ThreadingHTTPServer

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{httpd.server_address[1]}/api/scan",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return int(resp.status), json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode()
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                body = {"raw": raw}
            return int(exc.code), body
    finally:
        httpd.shutdown()
        httpd.server_close()


class AutomateHttpPost(unittest.TestCase):
    def test_demo_handler_implements_do_post(self) -> None:
        sys.path.insert(0, str(ROOT))
        from zeroguard.demo import DemoHandler  # noqa: E402

        self.assertTrue(callable(getattr(DemoHandler, "do_POST", None)))

    def test_post_scan_uncloneable_is_json_never_501(self) -> None:
        sys.path.insert(0, str(ROOT))
        from zeroguard.demo import DemoHandler  # noqa: E402

        status, body = _post_automate(
            DemoHandler, {"git_url": "/no/such/git/repo", "ref": "main", "path": "."}
        )
        self.assertNotEqual(status, 501, body)
        self.assertIn(status, (200, 400, 500), body)
        self.assertIsInstance(body, dict)
        self.assertIn("error", body)
