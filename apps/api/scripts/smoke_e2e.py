"""Black-box smoke test for custom-policy CRUD in offline mock mode."""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[3]
API_DIR = ROOT / "apps" / "api"


def request(base_url: str, path: str, *, method: str = "GET", payload: dict | None = None) -> tuple[int, object | None]:
    body = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if body else {}
    try:
        with urlopen(Request(f"{base_url}{path}", data=body, headers=headers, method=method), timeout=2) as response:
            body = response.read()
            return response.status, json.loads(body) if body else None
    except HTTPError as error:
        body = error.read()
        return error.code, json.loads(body) if body else None


def available_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def wait_for_health(base_url: str) -> None:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            status, body = request(base_url, "/health")
            if status == 200 and body == {"status": "ok"}:
                return
        except (URLError, ConnectionError, TimeoutError):
            pass
        time.sleep(0.2)
    raise RuntimeError("API did not become healthy within 15 seconds")


def main() -> None:
    temp_dir = Path(tempfile.mkdtemp(prefix="evelyn-smoke-"))
    port = available_port()
    base_url = f"http://127.0.0.1:{port}"
    token = f"Smoke policy {uuid4().hex}"
    environment = {
        **os.environ,
        "MODERATION_MODE": "mock",
        "POLICY_STORE_PATH": str(temp_dir / "policies.json"),
        "PYTHONPATH": str(API_DIR),
    }
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=API_DIR,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        wait_for_health(base_url)
        status, created = request(
            base_url,
            "/api/v1/policies",
            method="POST",
            payload={
                "name": token,
                "rule_text": "Synthetic policy used only by the E2E CRUD smoke test.",
                "violation_action": "BLOCK",
                "enabled": True,
            },
        )
        assert status == 201, created
        assert isinstance(created, dict)

        status, catalog = request(base_url, "/api/v1/policies")
        assert status == 200, catalog
        assert isinstance(catalog, dict)
        assert any(policy["rule_id"] == created["rule_id"] for policy in catalog["policies"])

        status, updated = request(
            base_url,
            f"/api/v1/policies/{created['rule_id']}",
            method="PATCH",
            payload={"enabled": False, "violation_action": "REVIEW"},
        )
        assert status == 200, updated
        assert isinstance(updated, dict)
        assert updated["rule_id"] == created["rule_id"]
        assert updated["enabled"] is False

        status, deleted = request(base_url, f"/api/v1/policies/{created['rule_id']}", method="DELETE")
        assert status == 204, deleted
        print("Custom-policy CRUD E2E smoke passed.")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        if process.returncode not in {0, -15}:  # pragma: no cover - shown only on smoke failure
            print(process.stderr.read(), file=sys.stderr)
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
