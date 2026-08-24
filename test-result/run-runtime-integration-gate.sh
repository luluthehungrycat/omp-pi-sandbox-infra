#!/usr/bin/env bash
set -euo pipefail

ROOT=${OMP_SANDBOX_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}
SOCKET=${OMP_BROKER_SOCKET:-/run/user/$(id -u)/omp-inference.sock}

if [[ ! -S "$SOCKET" ]]; then
  printf 'FAIL broker socket missing: %s\n' "$SOCKET" >&2
  exit 1
fi

printf '%s\n' '== Podman boundary probe =='
"$ROOT/test-result/portable-podman-boundary.sh" "$ROOT"

printf '%s\n' '== Adversarial sandbox tool-call probes =='
BWRAP_RESULTS=$(bun "$ROOT/test-result/run-bwrap-adversarial.ts")
printf '%s\n' "$BWRAP_RESULTS"
if printf '%s\n' "$BWRAP_RESULTS" | grep -q '"passed": false'; then
  printf 'FAIL adversarial sandbox probe\n' >&2
  exit 1
fi

printf '%s\n' '== Broker-backed contained inference =='
OMP_BROKER_SOCKET="$SOCKET" "$ROOT/test-result/run-omp-podman.sh" sh -c '
  set -eu
  bun /bridge.ts >/tmp/omp-inference-bridge.log 2>&1 &
  bridge=$!
  trap "kill $bridge 2>/dev/null || true" EXIT
  sleep 1
  output=$(bun /inference-smoke.ts)
  printf "%s\n" "$output"
  printf "%s\n" "$output" | grep -q BROKER_CONTAINER_OK
'

printf '%s\n' 'RUNTIME_INTEGRATION_PASS'
