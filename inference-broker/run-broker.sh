#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
SOCKET=${OMP_INFERENCE_SOCKET:-$ROOT/test-result/omp-inference.sock}
CONFIG=${OMP_BROKER_PROVIDER_CONFIG:-$ROOT/inference-broker/providers.example.json}

exec env \
  OMP_INFERENCE_SOCKET="$SOCKET" \
  OMP_BROKER_PROVIDER_CONFIG="$CONFIG" \
  OMP_LOCAL_BACKEND_HOST="${OMP_LOCAL_BACKEND_HOST:-127.0.0.1}" \
  OMP_LOCAL_BACKEND_PORT="${OMP_LOCAL_BACKEND_PORT:-8080}" \
  OMP_BROKER_TIMEOUT="${OMP_BROKER_TIMEOUT:-180}" \
  OMP_BROKER_MAX_IN_FLIGHT="${OMP_BROKER_MAX_IN_FLIGHT:-2}" \
  python3 "$ROOT/inference-broker/broker.py"
