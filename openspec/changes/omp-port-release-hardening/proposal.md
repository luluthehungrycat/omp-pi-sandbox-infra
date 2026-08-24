## Why

The three verified Pi-to-OMP ports are installable and published, but their release checks are duplicated across repositories and do not yet express a durable compatibility matrix or a single runtime integration contract. Gondolin also needs an explicit, evidence-backed compatibility track rather than an unsafe workaround.

## What Changes

- Define a shared OMP/Bun compatibility matrix for the verified ports.
- Consolidate public Git smoke and release verification around reusable infrastructure workflows.
- Treat public Git installation as the canonical no-token path and GitHub Packages as an optional authenticated path.
- Extend runtime validation with broker-backed container inference and package-loaded sandbox tool-call fixtures.
- Require the Podman containment boundary at release time.
- Track Gondolin's Bun/ssh2 native-module blocker and upstream report separately.

## Capabilities

### New Capabilities

- `omp-port-release-gates`: Repeatable installation, health, compatibility, runtime, and containment verification for OMP plugin releases.
- `omp-port-compatibility-matrix`: Explicit OMP/Bun version coverage with actionable failures.
- `omp-port-runtime-integration`: Package-loaded sandbox and broker-backed runtime validation under containment.

### Modified Capabilities

- `gondolin-bun-compatibility`: Remains blocked until `ssh2` loads without `uv_version_string` aborts under the supported OMP runtime.

## Impact

- `ROADMAP.md` files in the infrastructure and plugin repositories.
- `.github/workflows/` in the three verified package repositories and reusable workflows in infrastructure.
- `test-result/` runtime and containment harnesses.
- `openspec/changes/omp-port-release-hardening/` requirements and evidence.
