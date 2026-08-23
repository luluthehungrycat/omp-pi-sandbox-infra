#!/usr/bin/env python3
"""Subprocess-level operational checks for the host inference broker."""
from __future__ import annotations

import http.client
import http.server
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).parent
BROKER = ROOT / "broker.py"


class MockHandler(http.server.BaseHTTPRequestHandler):
    delay = 0.0

    def do_POST(self) -> None:
        if self.delay:
            time.sleep(self.delay)
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        body = json.dumps({"choices": [{"message": {"content": "ok"}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def log_message(self, *_args: object) -> None:
        pass


def mock_server() -> tuple[http.server.ThreadingHTTPServer, threading.Thread]:
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), MockHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def unix_request(socket_path: str, method: str, path: str, body: dict | None = None) -> tuple[int, bytes]:
    class UnixHTTP(http.client.HTTPConnection):
        def connect(self) -> None:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(socket_path)

    conn = UnixHTTP("broker", timeout=4)
    payload = None if body is None else json.dumps(body).encode()
    headers = {} if payload is None else {"Content-Type": "application/json"}
    conn.request(method, path, payload, headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()
    return response.status, data


def wait_health(socket_path: str, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if os.path.exists(socket_path):
            try:
                status, _ = unix_request(socket_path, "GET", "/health")
                if status == 200:
                    return
            except OSError:
                pass
        time.sleep(0.05)
    raise AssertionError("broker did not become healthy")


def start(env: dict[str, str]) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, str(BROKER)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def stop(proc: subprocess.Popen[str]) -> str:
    proc.terminate()
    output, _ = proc.communicate(timeout=5)
    return output


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="omp-broker-ops-") as temp:
        temp_path = Path(temp)
        sock = temp_path / "broker.sock"
        config = temp_path / "providers.json"
        upstream, _ = mock_server()
        upstream_url = f"http://127.0.0.1:{upstream.server_port}"
        config.write_text(json.dumps({"providers": {"mock": {
            "kind": "host-openai-chat",
            "base_url": upstream_url,
            "models": ["test-model"],
            "api_key_env": "OPS_SECRET",
        }}}))
        base = os.environ.copy()
        base.update({
            "OMP_INFERENCE_SOCKET": str(sock),
            "OMP_BROKER_PROVIDER_CONFIG": str(config),
            "OMP_LOCAL_BACKEND_PORT": str(upstream.server_port),
            "OMP_BROKER_TIMEOUT": "0.2",
            "OMP_BROKER_LOG_LEVEL": "INFO",
            "OPS_SECRET": "do-not-log-this-secret",
        })
        proc = start(base)
        try:
            wait_health(str(sock))
            status, _ = unix_request(str(sock), "GET", "/health")
            assert status == 200, status

            MockHandler.delay = 0.0
            status, body = unix_request(str(sock), "POST", "/v1/chat/completions", {
                "model": "mock/test-model", "messages": [{"role": "user", "content": "hello"}]
            })
            assert status == 200 and b'"ok"' in body, (status, body)

            MockHandler.delay = 1.0
            started = time.monotonic()
            status, _ = unix_request(str(sock), "POST", "/v1/chat/completions", {
                "model": "mock/test-model", "messages": []
            })
            elapsed = time.monotonic() - started
            assert status == 502 and elapsed < 0.8, (status, elapsed)
        finally:
            MockHandler.delay = 0.0
            logs = stop(proc)
            upstream.shutdown()
        assert not sock.exists(), "broker socket survived shutdown"
        assert "do-not-log-this-secret" not in logs, "credential leaked into broker logs"

        proc2 = start(base)
        try:
            wait_health(str(sock))
            status, _ = unix_request(str(sock), "GET", "/health")
            assert status == 200
        finally:
            stop(proc2)
        assert not sock.exists(), "broker socket survived restart shutdown"

    print("BROKER_OPERATIONAL_PASS")


if __name__ == "__main__":
    main()
