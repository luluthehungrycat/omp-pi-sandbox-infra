## Purpose

Define release gates for verified OMP plugin ports.

## ADDED Requirements

### Requirement: Public Git installation

Every verified release SHALL install through the public `github:` OMP plugin-manager path without a GitHub token.

#### Scenario: Clean public install

- **WHEN** a clean disposable HOME runs `omp plugin install github:owner/repository#release-tag`
- **THEN** installation, `omp plugin list`, and `omp plugin doctor` succeed

### Requirement: Authenticated package installation

Every published package release SHALL install from GitHub Packages with a token scoped only to the required package read operation in the consumer environment.

#### Scenario: Clean package install

- **WHEN** a clean disposable HOME maps the owner scope to `https://npm.pkg.github.com`
- **THEN** the tagged package installs and passes `omp plugin doctor`

### Requirement: Containment release gate

Every verified release SHALL pass the portable Podman boundary probe.

#### Scenario: Boundary remains closed

- **WHEN** the release verification job runs the rootless Podman probe
- **THEN** workspace writes pass, outside-root writes fail, host markers and Docker sockets are absent, and network access fails
