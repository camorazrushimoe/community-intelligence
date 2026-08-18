# Game Catalog

## ADDED Requirements

### Requirement: Game catalog schema

The system SHALL store a game catalog in PostgreSQL (table `games`) keyed by
`steam_app_id` (int, primary key), with `name`, `name_variants[]`, `genres[]`,
`tags[]`, `developer`, `publisher`, `release_date`, `price`, and `platforms[]`.

#### Scenario: Game is stored with a canonical identity

- **WHEN** a game is ingested into the catalog
- **THEN** it SHALL be keyed by `steam_app_id`
- **AND** `name` SHALL hold the canonical display name

#### Scenario: Name variants are recorded for matching

- **WHEN** a game has known aliases (e.g. "CS:GO", "csgo", "Counter-Strike")
- **THEN** the catalog SHALL store them in `name_variants[]`

### Requirement: Name matching

The system SHALL resolve a mention of a game (e.g. a Reddit text fragment) to a
catalog entry using `steam_app_id` + `name_variants`.

#### Scenario: Alias resolves to a catalog entry

- **WHEN** a signal mentions "RDR2"
- **THEN** the system SHALL match it to the catalog entry whose `name_variants`
  includes "RDR2"
- **AND** SHALL link the signal to that game's `steam_app_id`

#### Scenario: Unresolved mention is flagged, not dropped

- **WHEN** a mention matches no catalog entry
- **THEN** the system SHALL NOT silently drop it
- **AND** SHALL mark it as unmatched for later review

### Requirement: Catalog is idempotent

Re-importing the catalog SHALL NOT create duplicate game rows.

#### Scenario: Re-import does not duplicate

- **WHEN** a game already present by `steam_app_id` is imported again
- **THEN** the existing row SHALL be updated, not duplicated
