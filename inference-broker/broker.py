#!/usr/bin/env python3
"""Host-side inference broker for network-isolated OMP containers.

The client-visible protocol is a small OpenAI-compatible subset over a Unix
socket. Provider credentials and outbound networking remain on the host.

Provider config is optional and contains provider IDs, fixed base URLs, model
allowlists, and *environment variable names* for credentials. It must never
contain credential values.
"""
from __future__ import annotations

import http.client
import http.server
import json
import logging
import os
import select
import signal
import socket
import socketserver
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

SOCKET_PATH = Path(os.environ.get("OMP_INFERENCE_SOCKET", "/tmp/omp-inference.sock"))
LOCAL_HOST = os.environ.get("OMP_LOCAL_BACKEND_HOST", "127.0.0.1")
LOCAL_PORT = int(os.environ.get("OMP_LOCAL_BACKEND_PORT", "8080"))
LOCAL_MODEL = os.environ.get("OMP_LOCAL_MODEL", "LiquidAI_LFM2.5-2.6B-Q6_K_L")
MAX_BODY = int(os.environ.get("OMP_BROKER_MAX_BODY", str(2 * 1024 * 1024)))
REQUEST_TIMEOUT = float(os.environ.get("OMP_BROKER_TIMEOUT", "180"))
MAX_IN_FLIGHT = int(os.environ.get("OMP_BROKER_MAX_IN_FLIGHT", "2"))
CONFIG_PATH = Path(os.environ.get("OMP_BROKER_PROVIDER_CONFIG", "")) if os.environ.get("OMP_BROKER_PROVIDER_CONFIG") else None

logging.basicConfig(level=os.environ.get("OMP_BROKER_LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("omp-inference-broker")

ALLOWED_GET = {"/health", "/v1/models"}
ALLOWED_POST = {"/v1/chat/completions"}


@dataclass(frozen=True)
class Provider:
    provider_id: str
    kind: str
    base_url: str | None
    models: tuple[str, ...]
    api_key_env: str | None
    headers: dict[str, str]

    @property
    def public_models(self) -> list[str]:
        return [f"{self.provider_id}/{model}" for model in self.models]


def load_providers() -> dict[str, Provider]:
    providers: dict[str, Provider] = {
        "local": Provider("local", "local", None, (LOCAL_MODEL,), None, {})
    }
    if not CONFIG_PATH:
        return providers
    raw = json.loads(CONFIG_PATH.read_text())
    for provider_id, value in raw.get("providers", {}).items():
        if provider_id == "local":
            continue
        if not isinstance(value, dict):
            raise ValueError(f"provider {provider_id!r} must be an object")
        kind = str(value.get("kind", "openai-chat"))
        models = tuple(str(model) for model in value.get("models", []))
        base_url = value.get("base_url")
        if kind == "openai-chat" and (not isinstance(base_url, str) or not base_url.startswith("https://")):
            raise ValueError(f"remote provider {provider_id!r} requires an https base_url")
        if kind == "host-openai-chat":
            parsed = urlsplit(str(base_url or ""))
            if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
                raise ValueError(f"host provider {provider_id!r} must use http://127.0.0.1 or localhost")
        headers = value.get("headers", {})
        if not isinstance(headers, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in headers.items()):
            raise ValueError(f"provider {provider_id!r} headers must be string pairs")
        providers[provider_id] = Provider(provider_id, kind, base_url, models, value.get("api_key_env"), dict(headers))
    return providers


PROVIDERS = load_providers()
IN_FLIGHT = threading.BoundedSemaphore(MAX_IN_FLIGHT)


class UnixHTTPServer(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True
    allow_reuse_address = True


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        log.info("client=unix " + fmt, *args)

    def _error(self, status: int, message: str) -> None:
        body = json.dumps({"error": {"message": message, "type": "broker_error"}}).encode()
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
        except OSError:
            pass

    def _send_response(self, response: http.client.HTTPResponse) -> None:
        self.send_response(response.status, response.reason)
        for key, value in response.getheaders():
            if key.lower() in {"connection", "keep-alive", "transfer-encoding", "content-length"}:
                continue
            self.send_header(key, value)
        if response.getheader("Transfer-Encoding", "").lower() == "chunked":
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            while chunk := response.read(65536):
                self.wfile.write(f"{len(chunk):x}\r\n".encode() + chunk + b"\r\n")
            self.wfile.write(b"0\r\n\r\n")
        else:
            payload = response.read(MAX_BODY * 4)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    def _forward(self, provider: Provider, path: str, body: bytes = b"") -> None:
        if not IN_FLIGHT.acquire(blocking=False):
            self._error(429, "broker concurrency limit reached")
            return
        try:
            self._forward_inner(provider, path, body)
        finally:
            IN_FLIGHT.release()

    def _forward_inner(self, provider: Provider, path: str, body: bytes = b"") -> None:
        if provider.kind == "local":
            host, port, secure, upstream_path = LOCAL_HOST, LOCAL_PORT, False, path
        else:
            parsed = urlsplit(provider.base_url or "")
            host = parsed.hostname or ""
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            secure = parsed.scheme == "https"
            prefix = parsed.path.rstrip("/")
            upstream_path = prefix + path
        conn_cls = http.client.HTTPSConnection if secure else http.client.HTTPConnection
        conn = conn_cls(host, port, timeout=REQUEST_TIMEOUT)
        stop_watch = threading.Event()
        cancelled = threading.Event()

        def close_upstream() -> None:
            upstream_socket = conn.sock
            if upstream_socket is not None:
                try:
                    upstream_socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    upstream_socket.close()
                except OSError:
                    pass
            conn.close()

        def watch_client_disconnect() -> None:
            while not stop_watch.wait(0.05):
                try:
                    readable, _, _ = select.select([self.connection], [], [], 0)
                    if not readable:
                        continue
                    if not self.connection.recv(1, socket.MSG_PEEK):
                        log.info("provider=%s client disconnected; cancelling upstream request", provider.provider_id)
                        cancelled.set()
                        close_upstream()
                        return
                except OSError:
                    cancelled.set()
                    close_upstream()
                    return

        threading.Thread(target=watch_client_disconnect, name="broker-client-watch", daemon=True).start()
        headers = {"Accept": self.headers.get("Accept", "application/json")}
        headers.update(provider.headers)
        if provider.api_key_env:
            token = os.environ.get(provider.api_key_env)
            if not token:
                self._error(503, f"provider {provider.provider_id!r} credential is unavailable on broker host")
                return
            headers["Authorization"] = f"Bearer {token}"
        if body:
            headers["Content-Type"] = "application/json"
            headers["Content-Length"] = str(len(body))
        try:
            if cancelled.is_set():
                return
            conn.request("POST" if body else "GET", upstream_path, body=body or None, headers=headers)
            if cancelled.is_set():
                close_upstream()
                return
            self._send_response(conn.getresponse())
        except (OSError, TimeoutError, http.client.HTTPException) as exc:
            log.warning("provider=%s backend failure: %s", provider.provider_id, exc)
            if not self.wfile.closed:
                self._error(502, "inference provider unavailable")
        finally:
            stop_watch.set()
            conn.close()

    def do_GET(self) -> None:
        if self.path == "/health":
            body = json.dumps({"status": "ok", "providers": sorted(PROVIDERS)}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path != "/v1/models":
            self._error(404, "endpoint not available through broker")
            return
        models = []
        for provider in PROVIDERS.values():
            for model in provider.public_models:
                models.append({"id": model, "object": "model", "owned_by": provider.provider_id})
        body = json.dumps({"object": "list", "data": models}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/v1/chat/completions":
            self._error(404, "endpoint not available through broker")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._error(400, "invalid content length")
            return
        if length <= 0 or length > MAX_BODY:
            self._error(413, "request body exceeds broker limit")
            return
        try:
            request = json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            self._error(400, "request must be JSON")
            return
        if not isinstance(request, dict) or not isinstance(request.get("model"), str):
            self._error(400, "request must contain a model")
            return
        public_model = request["model"]
        if "/" in public_model:
            provider_id, model = public_model.split("/", 1)
            provider = PROVIDERS.get(provider_id)
            if not provider or model not in provider.models:
                self._error(403, "provider/model is not allowlisted by broker")
                return
            request["model"] = model
        elif public_model in {"local", "local-router", LOCAL_MODEL}:
            provider = PROVIDERS["local"]
            request["model"] = LOCAL_MODEL
        else:
            matches = [candidate for candidate in PROVIDERS.values() if public_model in candidate.models]
            if len(matches) != 1:
                self._error(403, "provider/model is not allowlisted or is ambiguous")
                return
            provider = matches[0]
        if not isinstance(request.get("messages"), list):
            self._error(400, "messages must be an array")
            return
        if isinstance(request.get("max_tokens"), int) and request["max_tokens"] > 8192:
            self._error(413, "max_tokens exceeds broker limit")
            return
        body = json.dumps(request, separators=(",", ":")).encode()
        self._forward(provider, self.path, body)


def main() -> None:
    SOCKET_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        SOCKET_PATH.unlink()
    except FileNotFoundError:
        pass
    server = UnixHTTPServer(str(SOCKET_PATH), Handler)
    os.chmod(SOCKET_PATH, 0o600)
    log.info("listening on %s providers=%s", SOCKET_PATH, ",".join(sorted(PROVIDERS)))

    def request_shutdown(_signum: int, _frame: Any) -> None:
        # shutdown() must run off the serve_forever thread to avoid deadlock.
        threading.Thread(target=server.shutdown, name="broker-shutdown", daemon=True).start()

    signal.signal(signal.SIGTERM, request_shutdown)
    signal.signal(signal.SIGINT, request_shutdown)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        try:
            SOCKET_PATH.unlink()
        except FileNotFoundError:
            pass


if __name__ == "__main__":
    main()
