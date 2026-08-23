#!/usr/bin/env python3
import http.client
import json
import os
import socket

SOCKET = os.environ.get("OMP_TEST_SOCKET", "/run/user/%s/omp-inference.sock" % os.getuid())

class UnixHTTP(http.client.HTTPConnection):
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(SOCKET)

def request(method, path, body=None):
    c = UnixHTTP("broker")
    data = None if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
    headers = {} if data is None else {"Content-Type": "application/json"}
    c.request(method, path, data, headers)
    r = c.getresponse()
    return r.status, r.read()

cases = [
    ("bad-json", request("POST", "/v1/chat/completions", b"{"), 400),
    ("unknown-model", request("POST", "/v1/chat/completions", {"model": "codex-oauth/not-allowed", "messages": []}), 403),
    ("oversized-output", request("POST", "/v1/chat/completions", {"model": "codex-oauth/gpt-5.5", "messages": [], "max_tokens": 8193}), 413),
    ("unknown-endpoint", request("POST", "/v1/anything", {"model": "codex-oauth/gpt-5.5", "messages": []}), 404),
]
for name, (status, body), expected in cases:
    print(name, status, "PASS" if status == expected else f"FAIL expected {expected}", body[:180].decode(errors="replace"))
    if status != expected:
        raise SystemExit(1)
