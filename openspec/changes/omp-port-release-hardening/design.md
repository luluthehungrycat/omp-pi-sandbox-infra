## Design

### Installation paths

The public GitHub `github:owner/repository#ref` path is the default because public repositories do not require package-registry credentials. GitHub Packages remains supported for consumers with `read:packages` access and is verified in release workflows using `GITHUB_TOKEN`.

### Workflow ownership

Infrastructure owns reusable workflow definitions. Package repositories provide only package-specific inputs: repository, package name, and verification policy. Release workflows must run public Git install, package install, `omp plugin doctor`, and the containment probe.

### Compatibility matrix

The matrix is explicit rather than inferred from a single local install. It covers supported OMP 18 releases and Bun versions, with package tests and plugin-manager smoke checks as the required signals.

### Runtime boundary

The host broker remains outside the untrusted container. The container receives only the approved Unix socket, while a loopback HTTP bridge translates requests. Podman uses network isolation, dropped capabilities, no-new-privileges, read-only root, resource limits, and a disposable writable workspace/home.

### Gondolin

Gondolin is not allowed an unsandboxed fallback. The current failure is a Bun native-module compatibility defect in `ssh2` (`uv_version_string`). The project records the reproduction and upstream issue; publication is blocked until a supported runtime/dependency combination passes.
