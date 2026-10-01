# Spec Delta

## Purpose

Define the observable release announcements behaviour of the UniFi announcer during its Rust migration and deployment.

## ADDED Requirements

### Requirement: Compatible releases
The service SHALL preserve deployed tag validation, application filtering, latest-per-tag selection, URLs, labels and escaped announcement formatting.

#### Scenario: Compatible releases
- **GIVEN** the configured UniFi release announcer
- **WHEN** A feed has applications and accessories for configured tags
- **THEN** Only the latest eligible application for each tag is selected and its message matches the Python oracle

### Requirement: Text and forum delivery
The service SHALL send text messages or create forum posts with starter messages and no mentions.

#### Scenario: Text and forum delivery
- **GIVEN** the configured UniFi release announcer
- **WHEN** An unseen release targets a supported text or forum channel
- **THEN** A matching message or forum starter is created

### Requirement: Parser and details
The service SHALL preserve parser fields and tag, stage and limit filtering, and expose release details.

#### Scenario: Parser and details
- **GIVEN** the configured UniFi release announcer
- **WHEN** A fixture file is parsed with filters
- **THEN** The output objects match the Python parser
