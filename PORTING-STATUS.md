# Pi-to-OMP port status

Date: 2026-08-22
Target: Oh My Pi 18.0.0, Bun 1.4.0

## Verified OMP ports

### pi-bash-wrap

Branch: `omp-port/bash-wrap`

Changes:

- switched extension and utility imports to OMP 18 APIs;
- used the injected `pi.typebox.Type` facade;
- removed obsolete `shellPath` options from OMP Bash tool definitions;
- updated shell-argument expectations for OMP's login-command mode;
- added fail-closed replacement Bash registration when bwrap is unavailable, incompatible, or the platform is unsupported;
- added OMP peer/development dependencies.

Verification:

- `bun run build`: PASS
- `bun test`: PASS, 49 passed / 0 failed
- direct OMP `loadExtensions()` factory load: PASS
- direct session-start registration harness: PASS; registered `bash` replacement plus `tool_call`

Security note: the fail-closed behavior is covered by implementation but still needs dedicated tests for missing/incompatible bwrap before this should be treated as a security-complete port.

### pi-sandbox-oddsjam

Branch: `omp-port/sandbox-oddsjam`

Changes:

- replaced legacy `getShellConfig` import with `@oh-my-pi/pi-utils/procmgr`;
- replaced synchronous legacy `SettingsManager.getShellPath()` use with `process.env.SHELL || /bin/sh`;
- removed obsolete OMP Bash `shellPath` option;
- added OMP utility/coding-agent development and peer dependencies.

Verification:

- `bun run typecheck`: PASS
- `bun test`: PASS, 157 passed / 0 failed
- direct OMP `loadExtensions()` factory load: PASS

Security note: existing configurable allowRead/allowWrite and allowedDomains settings remain intentionally powerful and require adversarial boundary testing.

### pi-sandbox-carderne

Branch: `omp-port/sandbox-carderne`

Changes:

- replaced legacy `getShellConfig` import with `@oh-my-pi/pi-utils/procmgr`;
- replaced synchronous legacy `SettingsManager.getShellPath()` use with `process.env.SHELL || /bin/sh`;
- removed obsolete OMP Bash `shellPath` option;
- added OMP utility/coding-agent development and peer dependencies.

Verification:

- `bun run check`: PASS
- `bun test`: PASS, 22 passed / 0 failed
- direct OMP `loadExtensions()` factory load: PASS

Security note: prompt/policy behavior is loaded, but filesystem/network adversarial tests are still required.

## Blocked / not yet ported

### pi-gondolin

Branch: `omp-port/gondolin`

Current upstream dependency remains `@earendil-works/gondolin ^0.4.0`; no functional source port was made.

Verification result: **BLOCKED**. The OMP loader process under Bun 1.4.0 aborts while loading Gondolin's `ssh2` native module:

`panic: unsupported uv function: uv_version_string`

This is a Bun/N-API compatibility failure before extension registration. Do not claim Gondolin loads or that its VM boundary works. Next port options are a Node-compatible OMP execution path, or a carefully tested Gondolin dependency/API upgrade.

## Global verification status

- TypeScript/package verification: PASS for the three addressed ports.
- OMP extension-loader verification: PASS for pi-bash-wrap, pi-sandbox-oddsjam, and pi-sandbox-carderne.
- Gondolin loader/runtime verification: BLOCKED by Bun native-module crash.
- OS-level containment/adversarial verification: PARTIAL; see the adversarial-stage results below.

## Adversarial stage results — 2026-08-22

Test workspace:

`/home/hermes/omp-sandbox-dev/`

The host Docker socket and active SSH-agent were detected during discovery but were not mounted or forwarded intentionally. All probes used the disposable `test-project`, `test-home`, and `test-result` paths.

### pi-bash-wrap hardened wrapper

Result: **PASS — 10/10 probes** after hardening.

Passed probes:

- writable project path;
- outside-project write denied;
- host secret hidden by private home mount;
- symlink escape denied;
- Docker socket hidden by private `/run` mount;
- SSH-agent socket unavailable;
- parent host PID unavailable after PID namespace isolation;
- `/dev/kvm` unavailable;
- network denied;
- nested `eval` remains inside the project boundary.

Additional verification:

- build: PASS;
- unit tests: 49/49 PASS;
- OMP `loadExtensions()`: PASS.

### sandbox-runtime ports

OddsJam and Carderne both produced the same result: **9/9 checks PASS**, with one observational finding.

Passed probes:

- writable project path;
- outside-project write denied;
- host secret hidden;
- Docker socket `connect()` denied by sandbox-runtime's default Linux Unix-socket seccomp policy;
- SSH-agent socket unavailable after wrapper environment sanitization;
- host PID unavailable;
- network denied;
- nested `eval` remains sandboxed.

Observational finding:

- `/var/run/docker.sock` remains path-visible inside the sandbox-runtime bwrap environment.

This does not establish Docker API access. A no-payload Unix-socket connection attempt is denied by seccomp. The host account also lacks permission to connect to the root-owned `0660` socket because it is not in the `docker` group.

Attempting to add `/var/run/docker.sock` to the runtime deny list causes the installed runtime to abort before command execution with `bwrap: Can't create file at /var/run/docker.sock`. Directory-level `/run`/`/var/run` denial likewise prevents runtime startup. No runtime patch is currently justified by the observed behavior.

Residual defense-in-depth considerations:

- retain the default Unix-socket seccomp policy;
- do not enable `allowAllUnixSockets` or allow the Docker socket explicitly;
- enforce `allowUnixSockets: []` and `allowAllUnixSockets: false` in the OMP adapter configuration;
- continue preferring an outer jail/container for high-risk unattended execution;
- rerun the connect probe if the runtime, host group membership, or socket permissions change.

The sandbox-runtime ports are not blocked solely because the socket pathname is visible, but they still require the broader external containment baseline for high-risk unattended use.

## Whole-process Podman baseline — 2026-08-22

Launcher:

`/home/hermes/omp-sandbox-dev/test-result/run-omp-podman.sh`

Verified launcher properties:

- rootless Podman 5.4.2;
- Bun 1.4.0 image;
- `--network=none`;
- `--userns=keep-id`;
- all capabilities dropped;
- `no-new-privileges`;
- read-only container root;
- disposable HOME mounted read/write;
- disposable project mounted read/write;
- plugin sources mounted read-only;
- no Docker/Podman socket mount;
- no SSH-agent environment or mount;
- resource limits: 256 PIDs, 2 GiB memory, 2 CPUs.

OMP loader verification inside the container:

- pi-bash-wrap: PASS;
- pi-sandbox-oddsjam: PASS;
- pi-sandbox-carderne: PASS.

Whole-process boundary probes:

- workspace write: PASS;
- outside-workspace write: DENIED;
- host home visibility: DENIED;
- Docker socket visibility: DENIED;
- SSH-agent visibility: DENIED;
- network/DNS access: DENIED;
- nested `eval` workspace write: PASS;
- host-path process inspection: DENIED.

The Podman launcher is now the preferred high-risk baseline. Native extensions should be tested inside it before any unattended or public packaging claim.

Kanban note: the Hermes Kanban CLI currently refused mutation from this session with `delegate_task child contexts cannot mutate Kanban tasks or boards`. The work is tracked in this workspace status document and the session task list; the Kanban database was not edited directly.

## Inference broker — 2026-08-22

Broker files:

- `inference-broker/broker.py`;
- `inference-broker/providers.example.json`;
- `inference-broker/README.md`;
- `test-result/unix-http-bridge.ts`.

Local end-to-end result: **PASS**.

- host llama-server remains on `127.0.0.1:8080`;
- broker listens on a Unix socket with mode `0600`;
- container mounts only that socket;
- container bridge exposes it as loopback-only `127.0.0.1:8090`;
- non-streaming chat: PASS;
- streaming SSE and `[DONE]`: PASS;
- model allowlist: PASS;
- unauthorized model: 403;
- missing remote credential: 503 without an outbound request.

Remote provider architecture:

- OpenRouter: implemented as a fixed HTTPS OpenAI-compatible route;
- OpenCode Go: implemented as a fixed HTTPS OpenAI-compatible route;
- models must be explicitly namespaced and allowlisted;
- credentials are read only from broker-host environment variables;
- Codex ChatGPT OAuth: intentionally fail-closed because the documented Codex authentication flow is client-managed and no stable third-party broker API contract was found.

Remote live calls remain **UNVERIFIED** until a user-authorized broker service environment supplies credentials. No credentials were read, copied, logged, or mounted.

## codex-as-api broker integration — 2026-08-22

Discovery:

- `/home/hermes/.local/bin/codex-as-api` is running as PID 840165;
- host listener is `0.0.0.0:18080`;
- `/health`: PASS, `auth_available: true`, model `gpt-5.5`;
- direct `/v1/chat/completions` contract: PASS with required system instructions;
- safe marker response: `CODEX_API_OK`.

Broker integration:

- `codex-oauth/gpt-5.5` is routed through the host broker to fixed `127.0.0.1:18080`;
- no Codex token or `auth.json` is read by the broker;
- the container does not receive port 18080 access or any credentials;
- OMP custom provider config is mounted only in the disposable container.

End-to-end results:

- raw container request through bridge: **PASS**, `CODEX_CONTAINER_OK`;
- OMP 18.0.0 CLI request through broker: **PASS**, `OMP_CODEX_BROKER_OK`;
- Codex broker streaming SSE: **PASS**, HTTP 200, `[DONE]` present;
- direct container access to `127.0.0.1:18080`: **DENIED**;
- malformed JSON: 400;
- unauthorized model: 403;
- excessive `max_tokens`: 413;
- unknown endpoint: 404.

Operational hardening:

- broker concurrency is bounded by `OMP_BROKER_MAX_IN_FLIGHT` (default 2);
- `inference-broker/run-broker.sh` provides a reproducible host launcher;
- `inference-broker/test_policy.py` covers broker rejection behavior.

## Remaining-step completion — 2026-08-22

### codex-as-api bind hardening

Updated `/home/hermes/.config/systemd/user/codex-as-api.service` from
`0.0.0.0` to `127.0.0.1`, reloaded systemd, and restarted the service.

Verification:

- service active: PASS;
- listener: `127.0.0.1:18080`;
- `/health`: PASS;
- inference through broker and isolated OMP: PASS.

### Broker service

Created and enabled:

`/home/hermes/.config/systemd/user/omp-inference-broker.service`

Properties:

- runtime socket: `%t/omp-inference.sock`;
- socket mode: `0600`;
- `NoNewPrivileges=true`;
- `PrivateTmp=true`;
- `PrivateDevices=true`;
- `ProtectSystem=strict`;
- `ProtectHome=read-only`;
- `RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6`;
- restart-on-failure;
- bounded broker concurrency: 2.

### Final verification

- broker policy suite: **PASS**;
- concurrency `[200, 429]`: **PASS**;
- client disconnect followed by broker health: **PASS**;
- OpenRouter without host credential: 503, no provider request;
- OpenCode Go without host credential: 503, no provider request;
- all three OMP extensions loaded inside the isolated container: **PASS**;
- OMP Codex request through the systemd-managed broker socket: **PASS**.

Remote OpenRouter/OpenCode Go live inference remains **UNVERIFIED** until their
credentials are deliberately provisioned to the host broker service. No
credentials were accessed or logged during this work.

### Combined gate and production configuration

- client disconnect now closes the broker's underlying upstream socket;
- slow-backend upstream cancellation regression: **PASS**;
- concurrency limit regression: **PASS**, `[200, 429]`;
- post-cancellation broker health: **PASS**;
- broken-client response handling no longer produces an unhandled traceback;
- default private provider config: `/home/hermes/.config/omp-inference-broker/providers.local.json`;
- default production providers: `local` and `codex-oauth` only;
- OpenRouter/OpenCode Go remain opt-in through `providers.example.json`;
- `codex-as-api.service`: active and loopback-only;
- `omp-inference-broker.service`: active with runtime socket mode `0600`;
- final production-style OMP request: **PASS**, `FINAL_PRODUCTION_PASS`.

## Follow-up release-candidate verification — 2026-08-23

### Package/install smoke tests

- pi-bash-wrap tarball extraction/import: **PASS**;
- pi-sandbox-oddsjam tarball extraction/import: **PASS**;
- pi-sandbox-carderne clean OMP-only install/import: **PASS**;
- Carderne package contents narrowed from 24 files / ~1.9 MB to 10 runtime/documentation files / ~56 KB;
- Carderne legacy runtime imports replaced with OMP 18 APIs;
- Carderne `bun run check`: **PASS**;
- Carderne tests: **22/22 PASS**.

### Broker operational hardening

`inference-broker/test_operational.py` now verifies with real subprocesses:

- health endpoint: **PASS**;
- successful host-provider forwarding: **PASS**;
- upstream timeout returns 502 within the configured bound: **PASS**;
- SIGTERM shutdown removes the Unix socket: **PASS**;
- restart recreates the socket and becomes healthy: **PASS**;
- credential value absent from broker logs: **PASS**.

### Gondolin current status

Gondolin remains **BLOCKED** and uncommitted. The current checkout reproduces an earlier-stage compatibility failure before native-module loading:

`Cannot find module '@mariozechner/pi-coding-agent'`

The checkout has an uncommitted OMP dependency experiment (`package.json`/`bun.lock`). No Gondolin containment or fallback behavior was changed. The previously documented Bun/native `uv_version_string` failure remains a separate follow-up once stale imports are resolved.

### Installed-package boundary verification

A fresh disposable Bun/OMP installation of all three packed release candidates was mounted read-only into a new rootless Podman container with `--network=none`, dropped capabilities, `no-new-privileges`, read-only root, resource limits, and only a disposable writable HOME. Each package loaded and completed broker-backed inference:

- installed pi-bash-wrap: **PASS**, `INSTALLED_BASH_WRAP`;
- installed pi-sandbox-oddsjam: **PASS**, `INSTALLED_ODDSJAM`;
- installed pi-sandbox-carderne: **PASS**, `INSTALLED_CARDERNE`.

This test caught and fixed a hidden OddsJam legacy runtime import that source-level tests had not exposed. OddsJam now uses OMP 18 runtime/type/UI imports, has no legacy peer dependencies, and passes `bun run typecheck` plus **157/157 tests**.

### Gondolin partial OMP port

The stale `@mariozechner/pi-coding-agent` imports were replaced with OMP 18 extension/shim imports and the OMP development dependency was recorded. The loader now reaches Gondolin's native dependency and fails reproducibly under Bun 1.4.0:

`panic: unsupported uv function: uv_version_string`

The crash occurs while loading `ssh2`'s `sshcrypto.node`, before extension registration. Gondolin remains **BLOCKED**. No unsandboxed fallback or containment weakening was added.

### GitHub publication verification

Published to `luluthehungrycat` SSH origins:

- `omp-pi-bash-wrap`, `main`, tag `v0.1.6`;
- `omp-pi-sandbox-oddsjam`, `main`, tag `v0.1.0`;
- `omp-pi-sandbox-carderne`, `main`, tag `v0.6.5`;
- `omp-pi-sandbox-infra`, `main`;
- `omp-pi-gondolin`, `main`, tag `v0.1.0`.

The first Bash-wrap tag exposed that built `dist/` output was ignored and absent from the Git repository. It was corrected in commit `e76087c`; `v0.1.6` now points to that commit. Fresh GitHub SSH installs/imports pass for all three OMP ports.

### GitHub Packages and CI — 2026-08-23

The verified packages now use the owner scope required by GitHub Packages:

- `@luluthehungrycat/omp-pi-bash-wrap`;
- `@luluthehungrycat/omp-pi-sandbox-oddsjam`;
- `@luluthehungrycat/omp-pi-sandbox-carderne`;
- Gondolin metadata is staged but remains unpublished because its runtime is blocked.

Each package declares both `pi.extensions` and `omp.extensions`. Each verified package has:

- Bun 1.4.0 test CI on `main` and pull requests;
- tag-triggered GitHub Packages publishing using repository-scoped `GITHUB_TOKEN` with `packages: write`;
- README instructions for GitHub Packages authentication and `omp plugin install`;
- no personal access token stored in the repository.

Published package workflow results:

- Bash-wrap `v0.1.8`: **PASS**;
- OddsJam `v0.1.1`: **PASS**;
- Carderne `v0.6.6`: **PASS**.

Bash-wrap's earlier `v0.1.7` workflow failed because its legacy `prepublishOnly` script attempted an npm/TypeScript rebuild without dev dependencies. The release workflow now uses the committed, independently tested `dist/` artifacts with `npm publish --ignore-scripts`. Legacy npm-publish workflows were removed from Bash-wrap and Carderne.

### GitHub Packages consumer verification — 2026-08-23

The publishing token at `~/.secrets/luluthehungrycat_publishingPAT.txt` was verified in memory only. It authenticates as `luluthehungrycat`, has `write:packages`, and exposes the three published packages as public GitHub Packages.

A disposable project with a temporary `.npmrc` successfully installed all three package versions with Bun 1.4.0. A separate disposable `HOME` with an isolated Bun cache successfully ran the actual OMP plugin manager:

- `omp plugin install @luluthehungrycat/omp-pi-bash-wrap@0.1.8`: **PASS**;
- `omp plugin install @luluthehungrycat/omp-pi-sandbox-oddsjam@0.1.1`: **PASS**;
- `omp plugin install @luluthehungrycat/omp-pi-sandbox-carderne@0.6.6`: **PASS**;
- `omp plugin list`: **PASS**, all three registered.

The first isolated OMP attempt encountered a transient `sharp` tarball integrity failure; retrying with a fresh Bun cache passed. No production `~/.omp`, credentials, or user data were modified.

