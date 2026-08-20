# Steam Collector

## ADDED Requirements

### Requirement: New-release discovery

The collector SHALL discover games that released, or entered Early Access, within
a **sliding window** of `DISCOVERY_WINDOW_DAYS` (default 30) on every run. It SHALL
obtain candidates from `IStoreService/GetAppList` (Steam Web API key), filtered by
`last_modified`, and SHALL verify each candidate's exact release date against
`appdetails`.

#### Scenario: A fresh release is discovered

- **WHEN** a candidate's `release_date.coming_soon` is false and `release_date.date`
  falls within the sliding window
- **THEN** the collector SHALL treat it as a discovery candidate

#### Scenario: Early Access counts as a release

- **WHEN** a candidate's `genres` includes `"Early Access"`
- **THEN** the collector SHALL treat its Early Access launch date as the release
  date for discovery purposes

#### Scenario: A candidate below the gate is retried within the window

- **WHEN** a candidate fails the quality gate
- **THEN** the collector SHALL re-evaluate it on subsequent runs for as long as its
  release date remains inside the window

### Requirement: Quality gate (entry only)

The collector SHALL admit a discovered game into the catalog only when it clears a
minimum quality bar. The bar SHALL be applied **only at admission time**: once a
game is in the catalog, it SHALL be collected regardless of how its reviews evolve
(a quality decay is a signal, not a removal reason).

#### Scenario: A candidate below the threshold is skipped

- **WHEN** a candidate has fewer than `MIN_REVIEWS` (default 50) total reviews OR a
  review score worse than `MIN_SCORE` (default "Mixed")
- **THEN** the collector SHALL NOT add it to the catalog

#### Scenario: Review quality decays after admission

- **WHEN** a catalog game's score drops from positive to negative (e.g.
  "Very Positive" → "Overwhelmingly Negative")
- **THEN** the collector SHALL keep collecting it
- **AND** SHALL NOT remove it from the catalog

### Requirement: Catalog enrichment

The collector SHALL populate catalog metadata for each known `steam_app_id` from
`appdetails`, including `name`, `genres`, `tags`, `developer`, `publisher`,
`release_date`, `price`, and `platforms`.

#### Scenario: Metadata is stored

- **WHEN** a game is admitted or re-synced
- **THEN** the collector SHALL upsert the `games` row keyed by `steam_app_id` with
  metadata from `appdetails`

### Requirement: Review ingestion

The collector SHALL pull English-language reviews from
`store.steampowered.com/appreviews` and write them to `signals` with
`source = 'steam_review'`.

#### Scenario: A review becomes a signal

- **WHEN** a review is fetched
- **THEN** the collector SHALL write a `signals` row with `source='steam_review'`,
  `source_id`, `text_raw`, `author`, `timestamp`, and `game_ref`
- **AND** SHALL preserve `score` from helpful votes where available

#### Scenario: Review is linked to the catalog

- **WHEN** a review is stored
- **THEN** `game_ref` SHALL reference the matching `games.steam_app_id`

### Requirement: Incremental collection

The collector SHALL collect incrementally: discovery SHALL re-scan the sliding
window on each run but SHALL NOT duplicate already-admitted games, and review
ingestion SHALL use a per-game cursor.

#### Scenario: Only new reviews are fetched

- **WHEN** the collector re-runs
- **THEN** it SHALL fetch only reviews newer than the last cursor
- **AND** SHALL NOT re-insert previously stored reviews

#### Scenario: Already-admitted games are not re-discovered

- **WHEN** a game is already present in the catalog by `steam_app_id`
- **THEN** discovery SHALL NOT create a duplicate row (idempotent upsert)

### Requirement: Rate limiting

The collector SHALL throttle its requests to Steam to respect rate limits, and
SHALL back off and retry on rate-limit (429) and transient server (5xx) errors.

#### Scenario: Rate limit is respected

- **WHEN** the collector issues requests to Steam
- **THEN** it SHALL NOT exceed the configured rate (default 200 requests / 5 minutes)
- **AND** SHALL retry with exponential backoff on rate-limit errors

### Requirement: Collector state

The collector SHALL persist its state in a `collector_state` table: the last
discovery run timestamp, per-game review cursors, and last-checked markers for
deferred candidates.

#### Scenario: State survives restarts

- **WHEN** the collector restarts
- **THEN** it SHALL resume from persisted state rather than re-scanning from scratch
