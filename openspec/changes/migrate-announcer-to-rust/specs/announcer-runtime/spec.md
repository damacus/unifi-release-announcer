# Spec Delta

## Purpose

Define the observable announcer runtime behaviour of the UniFi announcer during its Rust migration and deployment.

## ADDED Requirements

### Requirement: HTTP polling and shutdown
The service SHALL poll without Gateway or cache, immediately then every ten minutes, and handle termination within 30 seconds.

#### Scenario: HTTP polling and shutdown
- **GIVEN** the configured UniFi release announcer
- **WHEN** A poll fails or the service receives SIGTERM
- **THEN** Recoverable failures leave later polls possible and termination stops the loop within the bound

### Requirement: Dry-run and configuration
The service SHALL accept existing environment variables, validate them at startup, and provide --once and --dry-run.

#### Scenario: Dry-run and configuration
- **GIVEN** the configured UniFi release announcer
- **WHEN** Dry-run executes with valid configuration
- **THEN** Candidate decisions are emitted and Discord receives no writes

### Requirement: Memory and rollout
The release container SHALL use at most 32 MiB idle and 64 MiB peak working-set memory in a 24-hour test and SHALL replace production through a single-writer Recreate rollout.

#### Scenario: Memory and rollout
- **GIVEN** the configured UniFi release announcer
- **WHEN** The candidate completes live-history polling and is deployed last
- **THEN** Memory meets both thresholds, existing announcements are not repeated and the previous digest remains available for rollback
