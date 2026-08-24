## 1. Repository tracking

- [x] 1.1 Add infrastructure and per-plugin `ROADMAP.md` files.
- [x] 1.2 Record public Git and GitHub Packages installation policy.
- [x] 1.3 Record Gondolin's separate blocked status.

## 2. Release and compatibility gates

- [x] 2.1 Add public Git plugin-manager smoke workflows.
- [x] 2.2 Add GitHub Packages release verification.
- [x] 2.3 Add portable Podman containment verification.
- [x] 2.4 Add host-side broker-backed container inference verification.
- [x] 2.5 Consolidate duplicated package workflows into reusable infrastructure workflows.
- [x] 2.6 Add and execute the OMP/Bun compatibility matrix.

## 3. Runtime integration

- [x] 3.1 Verify the broker socket and HTTP bridge under rootless Podman.
- [x] 3.2 Verify a real container inference response (`BROKER_CONTAINER_OK`).
- [x] 3.3 Add adversarial sandbox tool-call fixtures to the runtime gate.
- [ ] 3.4 Promote broker-backed runtime integration to a hosted required release status check once CI provides the approved broker service.

## 4. Gondolin

- [x] 4.1 Test the current port under Bun 1.4.0.
- [x] 4.2 Test latest Gondolin 0.12.0.
- [x] 4.3 Confirm `ssh2` 1.17.0 and `uv_version_string` are the blocker.
- [x] 4.4 Record Bun issue #18546 and prohibit unsafe fallbacks.
- [ ] 4.5 Re-test after an upstream Bun/Gondolin/ssh2 compatibility release.

## 5. Evidence

- [x] 5.1 Run Bash-wrap build and 49 tests after documentation update.
- [x] 5.2 Keep package/repository worktrees clean after each release change.
- [x] 5.3 Close completed tasks only with CI URLs or reproducible local command output; leave genuine upstream blockers open.
