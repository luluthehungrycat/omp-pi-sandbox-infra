#!/usr/bin/env bash
set -euo pipefail

WORKSPACE=${1:?usage: portable-podman-boundary.sh WORKSPACE}
IMAGE=${BOUNDARY_IMAGE:-docker.io/library/alpine:3.20}
HOST_MARKER=$(mktemp /tmp/omp-boundary-host-marker.XXXXXX)
trap 'rm -f "$HOST_MARKER"' EXIT
printf 'host-only\n' > "$HOST_MARKER"

podman pull "$IMAGE" >/dev/null
podman run --rm \
  --userns=keep-id \
  --network=none \
  --cap-drop=all \
  --security-opt=no-new-privileges \
  --read-only \
  --pids-limit=128 \
  --memory=256m \
  --cpus=1 \
  --env HOME=/sandbox-home \
  --env HOST_MARKER=/host-only-marker \
  --volume "$WORKSPACE:/workspace:rw" \
  --tmpfs /tmp:rw,noexec,nosuid,nodev \
  --workdir /workspace \
  "$IMAGE" sh -eu -c '
    printf "workspace-write\n" > /workspace/.omp-boundary-write
    test "$(cat /workspace/.omp-boundary-write)" = workspace-write
    rm /workspace/.omp-boundary-write

    if touch /outside-root-write 2>/dev/null; then
      echo "FAIL outside-root-write" >&2
      exit 1
    fi
    test ! -e "$HOST_MARKER"
    test ! -e /var/run/docker.sock

    if wget -q -T 2 -O /tmp/network-probe https://example.com 2>/dev/null; then
      echo "FAIL network-access" >&2
      exit 1
    fi

    printf "BOUNDARY_PASS\n"
  '
