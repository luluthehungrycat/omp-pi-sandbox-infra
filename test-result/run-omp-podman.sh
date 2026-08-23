#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/hermes/omp-sandbox-dev
IMAGE=${OMP_PODMAN_IMAGE:-docker.io/oven/bun:1.4.0}
BROKER_SOCKET=${OMP_BROKER_SOCKET:-$ROOT/test-result/omp-inference.sock}

exec podman run --rm \
  --name omp-sandbox-dev-run \
  --userns=keep-id \
  --network=none \
  --cap-drop=all \
  --security-opt=no-new-privileges \
  --read-only \
  --pids-limit=256 \
  --memory=2g \
  --cpus=2 \
  --env HOME=/sandbox-home \
  --env XDG_CONFIG_HOME=/sandbox-home/.config \
  --env XDG_DATA_HOME=/sandbox-home/.local/share \
  --env XDG_STATE_HOME=/sandbox-home/.local/state \
  --env XDG_CACHE_HOME=/sandbox-home/.cache \
  --env OMP_INFERENCE_SOCKET=/run/omp-inference.sock \
  --env OMP_INFERENCE_BRIDGE_PORT=8090 \
  --unsetenv SSH_AUTH_SOCK \
  --unsetenv SSH_AGENT_PID \
  --unsetenv DOCKER_HOST \
  --volume "$ROOT/test-home:/sandbox-home:rw" \
  --volume "$ROOT/test-project:/workspace:rw" \
  --volume "$ROOT/plugins/pi-bash-wrap:/plugins/pi-bash-wrap:ro" \
  --volume "$ROOT/plugins/pi-sandbox-oddsjam:/plugins/pi-sandbox-oddsjam:ro" \
  --volume "$ROOT/plugins/pi-sandbox-carderne:/plugins/pi-sandbox-carderne:ro" \
  --volume "$ROOT/plugins/pi-gondolin:/plugins/pi-gondolin:ro" \
  --volume "$BROKER_SOCKET:/run/omp-inference.sock:rw" \
  --volume "$ROOT/test-result/unix-http-bridge.ts:/bridge.ts:ro" \
  --volume "$ROOT/test-result/container-inference-smoke.ts:/inference-smoke.ts:ro" \
  --volume "$ROOT/test-result/container-inference-stream-smoke.ts:/inference-stream-smoke.ts:ro" \
  --volume "$ROOT/test-result/container-codex-smoke.ts:/codex-smoke.ts:ro" \
  --volume "$ROOT/test-result/omp-models.yml:/sandbox-home/.omp/agent/models.yml:ro" \
  --volume "$ROOT/test-result/container-codex-stream.ts:/codex-stream.ts:ro" \
  --volume "/home/hermes/.bun/bin/omp:/usr/local/bin/omp:ro" \
  --volume "/home/hermes/.bun/install/global/node_modules:/usr/local/node_modules:ro" \
  --workdir /plugins/pi-bash-wrap \
  "$IMAGE" "$@"
