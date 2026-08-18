# API & Dashboard (MVP)

## ADDED Requirements

### Requirement: Sentiment trend endpoint

The API SHALL expose a JSON endpoint returning the 30-day sentiment trend for a game.

#### Scenario: Trend is returned

- **WHEN** a client requests the sentiment trend for a game
- **THEN** the API SHALL return per-day sentiment over the last 30 days
- **AND** the response SHALL be valid JSON

### Requirement: Top-5 pain topics endpoint

The API SHALL expose the top-5 pain topics per game.

#### Scenario: Top pains are returned

- **WHEN** a client requests top pains for a game
- **THEN** the API SHALL return the top-5 topics ranked by negative-sentiment volume

### Requirement: Agent-native output

The API SHALL be consumable by both humans (dashboard) and AI agents
(structured JSON).

#### Scenario: Machine-readable response

- **WHEN** an agent queries the API
- **THEN** responses SHALL be structured JSON, not rendered HTML

### Requirement: Minimal surface

The MVP SHALL expose only the endpoints above (FastAPI), with an optional simple
dashboard on top.

#### Scenario: MVP is minimal

- **WHEN** the MVP ships
- **THEN** it SHALL provide at minimum the sentiment-trend and top-pains endpoints
  per game
