## Purpose

Track Gondolin's native-runtime compatibility without weakening isolation.

## ADDED Requirements

### Requirement: No unsafe Gondolin fallback

Gondolin SHALL NOT bypass its VM, network policy, or native-loader failure by falling back to unsandboxed tool execution.

#### Scenario: Native blocker remains

- **WHEN** Bun aborts while loading `ssh2` with `unsupported uv function: uv_version_string`
- **THEN** the port remains blocked and unpublished, with the reproduction and upstream issue recorded

### Requirement: Compatibility release re-test

Gondolin SHALL be re-tested after a Bun, Gondolin, or ssh2 release claims the missing libuv compatibility.

#### Scenario: Candidate fix

- **WHEN** a candidate dependency/runtime combination is selected
- **THEN** the extension import, registration, VM startup, network policy, and tool execution all pass before publication is reconsidered
