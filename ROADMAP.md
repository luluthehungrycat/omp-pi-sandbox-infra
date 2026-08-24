# Pi-to-OMP Port Roadmap

## Purpose

Track the verified migration of selected Pi extensions to OMP 18 while preserving package reproducibility, public no-token installation, GitHub Packages publication, and the host-side inference-broker/Podman containment boundary.

## Status

### Completed

- [x] Port Bash-wrap, OddsJam, and Carderne to OMP 18 imports and manifests.
- [x] Publish verified packages to GitHub Packages.
- [x] Make public `github:` installation the canonical no-token path.
- [x] Add Bun test CI, public Git plugin smoke CI, and release verification.
- [x] Verify Git and GitHub Packages installation with `omp plugin doctor`.
- [x] Add portable Podman boundary gate.
- [x] Run the host-side broker-backed container inference smoke test: `BROKER_CONTAINER_OK`.
- [x] Update Bash-wrap Development documentation from the original Pi/npm instructions.

### In progress

- [x] Consolidate duplicated package workflows into reusable infrastructure workflows.
- [x] Add and execute an OMP/Bun compatibility matrix covering OMP 18.0.0/18.0.4 on Bun 1.4.0.
- [x] Add the broker-backed runtime integration gate and make it part of release verification.
- [x] Prepare the Gondolin/Bun native-module compatibility report for upstream submission.
- [x] Add adversarial sandbox tool-call fixtures to the runtime gate.

### Release policy

A verified package release requires unit/type checks, public Git installation, GitHub Packages installation, plugin health checks, and the Podman containment gate. Do not publish Gondolin until its native loader passes under the supported OMP runtime.

## OpenSpec

The active design and requirements are tracked in:

`openspec/changes/omp-port-release-hardening/`

See its `tasks.md` for implementation evidence and remaining work.
