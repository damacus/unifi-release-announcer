# Spec Delta

## Purpose

Define the observable announcement reliability behaviour of the UniFi announcer during its Rust migration and deployment.

## ADDED Requirements

### Requirement: Bounded history
The service SHALL inspect 200 recent text messages or active forum starters and 50 archived forum starters.

#### Scenario: Bounded history
- **GIVEN** the configured UniFi release announcer
- **WHEN** An announcement is on the second text page or in an archived forum starter
- **THEN** Its release URL is detected and skipped

### Requirement: History failure
The service SHALL skip posting if any required history request fails.

#### Scenario: History failure
- **GIVEN** the configured UniFi release announcer
- **WHEN** History returns a timeout or permission error
- **THEN** No announcement is sent during that poll

### Requirement: Unique URLs and send outcomes
The service SHALL send each candidate URL at most once per poll and SHALL NOT blindly retry an uncertain POST.

#### Scenario: Unique URLs and send outcomes
- **GIVEN** the configured UniFi release announcer
- **WHEN** Two tags select one URL or a send times out after delivery
- **THEN** The URL is attempted once and a later poll reconciles history before further posting
