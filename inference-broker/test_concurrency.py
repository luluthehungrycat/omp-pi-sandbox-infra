#!/usr/bin/env python3
from __future__ import annotations

import concurrent.futures
import http.client
import http.server
import json
import os
import select
import socket
import subprocess
import tempfile
import threading
import time
from pathlib import Path

class SlowBackend(http.server.ThreadingHTTPServer):
    allow_reuse_address = True

class Backend(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        time.sleep(1.0)
        readable, _, _ = select.select([self.connection], [], [], 0)
        if readable and not self.connection.recv(1, socket.MSG_PEEK):
            self.server.cancelled = True
            return
        body = json.dumps({"choices": [{"message": {"role": "assistant", "content": "OK"}, "finish_reason": "stop", "index": 0}], "object": "chat.completion"}).encode()
        try:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except BrokenPipeError:
            self.server.cancelled = True
    def do_GET(self):
        body = b'{"status":"ok"}'
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

class UnixHTTP(http.client.HTTPConnection):
    def __init__(self, path):
        super().__init__("broker")
        self.path = path
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.path)

def call(sock_path):
    conn = UnixHTTP(sock_path)
    body = json.dumps({"model": "local-router", "messages": [{"role": "user", "content": "test"}], "max_tokens": 1})
    conn.request("POST", "/v1/chat/completions", body, {"Content-Type": "application/json"})
    response = conn.getresponse()
    return response.status, response.read()

def main():
    backend = SlowBackend(("127.0.0.1", 0), Backend)
    backend.cancelled = False
    threading.Thread(target=backend.serve_forever, daemon=True).start()
    with tempfile.TemporaryDirectory(prefix="omp-broker-test-") as directory:
        sock_path = str(Path(directory) / "broker.sock")
        env = os.environ.copy()
        for key in ("OMP_BROKER_PROVIDER_CONFIG",):
            env.pop(key, None)
        env.update({
            "OMP_INFERENCE_SOCKET": sock_path,
            "OMP_LOCAL_BACKEND_PORT": str(backend.server_address[1]),
            "OMP_BROKER_MAX_IN_FLIGHT": "1",
            "OMP_BROKER_TIMEOUT": "10",
        })
        broker = subprocess.Popen(["python3", "broker.py"], cwd=Path(__file__).parent, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            deadline = time.time() + 5
            while not os.path.exists(sock_path):
                if broker.poll() is not None:
                    raise RuntimeError(broker.stdout.read())
                if time.time() > deadline:
                    raise TimeoutError("broker socket did not appear")
                time.sleep(0.05)
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: call(sock_path), range(2)))
            statuses = sorted(status for status, _ in results)
            print("concurrency", statuses, "PASS" if statuses == [200, 429] else "FAIL")
            if statuses != [200, 429]:
                raise SystemExit(1)

            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.connect(sock_path)
            cancel_body = b'{"model":"local-router","messages":[{"role":"user","content":"cancel"}],"max_tokens":1}'
            client.sendall(
                b"POST /v1/chat/completions HTTP/1.1\r\nHost: broker\r\nContent-Length: "
                + str(len(cancel_body)).encode()
                + b"\r\nContent-Type: application/json\r\n\r\n"
                + cancel_body
            )
            client.close()
            time.sleep(1.2)
            print("upstream-cancelled", backend.cancelled, "PASS" if backend.cancelled else "INCONCLUSIVE")
            if not backend.cancelled:
                raise SystemExit(1)
            conn = UnixHTTP(sock_path)
            conn.request("GET", "/health")
            response = conn.getresponse()
            print("disconnect-health", response.status, "PASS" if response.status == 200 else "FAIL")
            if response.status != 200:
                raise SystemExit(1)
        finally:
            broker.terminate()
            broker.wait(timeout=5)
            if broker.stdout:
                print("broker-log", broker.stdout.read())
            backend.shutdown()

if __name__ == "__main__":
    main()
