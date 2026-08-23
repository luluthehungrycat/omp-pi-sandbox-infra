# Host-side inference broker

`broker.py` exposes a constrained OpenAI-compatible API over a Unix socket. The
container receives only that socket; the broker owns all outbound networking
and provider credentials.

## Local-only mode

```bash
OMP_INFERENCE_SOCKET=/run/user/$(id -u)/omp-inference.sock \
OMP_LOCAL_BACKEND_PORT=8080 \
python3 broker.py
```

## Remote-provider mode

Copy `providers.example.json` to a private configuration path and edit the
model allowlists. Keep only environment-variable names in the file. Export
credentials in the broker service environment, never in the OMP container:

```bash
export OPENROUTER_API_KEY='[REDACTED]'
export OPENCODE_GO_API_KEY='[REDACTED]'
export OMP_BROKER_PROVIDER_CONFIG=/private/path/providers.json
python3 broker.py
```

Public model IDs are namespaced:

```text
local/LiquidAI_LFM2.5-2.6B-Q6_K_L
openrouter/openai/gpt-5.2
opencode-go/kimi-k3
codex-oauth/gpt-5.5
```

The broker rejects arbitrary providers, models, URLs, methods, and client
headers. It forwards only fixed HTTPS provider URLs and an injected host-side
Authorization header.

## Codex OAuth through codex-as-api

If the separately managed host-side `codex-as-api` service is running on
`127.0.0.1:18080`, the example config routes `codex-oauth/gpt-5.5` to it as a
fixed host-loopback OpenAI-compatible backend. The broker never reads or copies
Codex tokens, and the container sees only the broker socket.

This is intentionally an adapter to the local `codex-as-api` service, not a
direct implementation of the undocumented ChatGPT OAuth backend. Keep
`codex-as-api` bound to host loopback or protect it with an equivalent host
boundary; do not expose port 18080 to the container or public network.
