## Purpose

Define supported OMP/Bun combinations for the verified ports.

## ADDED Requirements

### Requirement: Explicit compatibility matrix

CI SHALL test each verified port against the declared OMP 18 and Bun versions rather than relying on one local installation.

#### Scenario: Supported combination passes

- **WHEN** a matrix job selects a supported OMP 18 release and Bun version
- **THEN** package tests, public Git plugin installation, and plugin health checks pass

#### Scenario: Unsupported combination is visible

- **WHEN** a matrix job encounters an import, native dependency, or registration failure
- **THEN** the job reports the exact OMP/Bun/package combination and does not silently downgrade the result
