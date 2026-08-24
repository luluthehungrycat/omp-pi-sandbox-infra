## Purpose

Define runtime evidence for the host-side inference broker and future package-loaded sandbox calls.

## ADDED Requirements

### Requirement: Broker-backed container inference

The runtime gate SHALL exercise a real inference request from the contained environment through the approved Unix-socket broker bridge.

#### Scenario: Container reaches broker only through bridge

- **WHEN** the rootless network-isolated container runs the inference smoke request
- **THEN** it receives HTTP 200 and the expected `BROKER_CONTAINER_OK` response without exposing host credentials

### Requirement: Package-loaded sandbox runtime

The runtime gate SHALL eventually load each verified extension package and exercise representative sandboxed tool calls inside the containment fixture.

#### Scenario: Package runtime preserves policy

- **WHEN** an installed extension performs an allowed workspace operation and denied outside-root/network operations
- **THEN** the allowed operation succeeds and denied operations remain denied
