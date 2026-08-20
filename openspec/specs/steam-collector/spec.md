# Steam Collector

## ADDED Requirements

### Requirement: Signals schema

The collector SHALL create and own the Level-2 `signals` table so every signal
(review, post, comment) has one shared, stable home. The table SHALL enforce
`UNIQUE (source, source_id)` and a foreign key `game_ref` referencing
`games.steam_app_id`.

#### Scenario: Signals are uniquely identified across sources

- **WHEN** a signal is stored
- **THEN** it SHALL be keyed by the pair `(source, source_id)`
- **AND** re-ingesting the same `(source, source_id)` SHALL NOT create a duplicate row

#### Scenario: Signals link to the catalog

- **WHEN** a signal references a game
- **THEN** `game_ref` SHALL be a foreign key to `games.steam_app_id`

### Requirement: New-release discovery

The collector SHALL discover games that released, or entered Early Access, within
a sliding window of `DISCOVERY_WINDOW_DAYS` (default 30) on every run. It SHALL
obtain candidates from `IStoreService/GetAppList` (Steam Web API key), filtered by
`last_modified`, verify the exact release date against `appdetails`, and SHALL
re-check gate-failing candidates on subsequent runs for as long as their release
date remains inside the window.

#### Scenario: A fresh release is discovered

- **WHEN** a candidate's `release_date.coming_soon` is false and `release_date.date`
  falls within the sliding window `[now − 30d, now]` (inclusive, UTC)
- **THEN** the collector SHALL treat it as a discovery candidate

#### Scenario: A not-yet-released game is excluded

- **WHEN** a candidate's `release_date.coming_soon` is true
- **THEN** the collector SHALL NOT treat it as a release

#### Scenario: A stale release date is excluded

- **WHEN** a candidate's `last_modified` is inside the window but `release_date.date`
  is older than the window (a patch/price change)
- **THEN** the collector SHALL NOT treat it as a new release

#### Scenario: Early Access counts as a release

- **WHEN** a candidate's `genres` includes `"Early Access"`
- **THEN** the collector SHALL treat `release_date.date` as its release date

#### Scenario: A gate-failing candidate is retried within the window

- **WHEN** a candidate fails the quality gate
- **THEN** the collector SHALL persist its `steam_app_id` as deferred
- **AND** SHALL re-evaluate it on every subsequent run while its `release_date.date`
  remains inside the window

### Requirement: Quality gate (entry only)

The collector SHALL admit a discovered game into the catalog only when it clears a
minimum quality bar, evaluated **before** the game is upserted. The bar SHALL be
applied **only at admission time**: once a game is in the catalog, it SHALL be
collected regardless of how its reviews evolve (a quality decay is a signal, not a
removal reason).

#### Scenario: A candidate below the threshold is skipped

- **WHEN** a candidate has fewer than `MIN_REVIEWS` (default 50) total reviews OR a
  review score worse than `MIN_SCORE` (default "Mixed")
- **THEN** the collector SHALL NOT add it to the catalog

#### Scenario: Boundaries are inclusive

- **WHEN** a candidate has exactly `MIN_REVIEWS` reviews and a score of exactly
  `MIN_SCORE`
- **THEN** the collector SHALL admit it

#### Scenario: Gate precedes enrichment

- **WHEN** a candidate is discovered
- **THEN** the gate SHALL be evaluated before the game is upserted into `games`

#### Scenario: Review quality decays after admission

- **WHEN** a catalog game's score drops from positive to negative (e.g.
  "Very Positive" → "Overwhelmingly Negative")
- **THEN** the collector SHALL keep collecting it
- **AND** SHALL NOT remove it from the catalog

### Requirement: Catalog enrichment

The collector SHALL populate catalog metadata for each known `steam_app_id` from
`appdetails`: `name`, `genres`, `developer`, `publisher`, `release_date`, `price`,
and `platforms`. (`tags` are not available from `appdetails` and SHALL be left
empty on this change.)

#### Scenario: Metadata is stored

- **WHEN** a game is admitted or re-synced
- **THEN** the collector SHALL upsert the `games` row keyed by `steam_app_id` with
  metadata from `appdetails`

#### Scenario: Price is stored in cents; free games are zero

- **WHEN** a game has a `price_overview`
- **THEN** the collector SHALL store `price_overview.final` (integer cents) in `games.price`
- **AND WHEN** a game has no `price_overview` (free-to-play)
- **THEN** it SHALL store `price = 0`

#### Scenario: Platforms are canonical booleans

- **WHEN** `appdetails.platforms.{windows,mac,linux}` is true
- **THEN** the collector SHALL store the corresponding label (`windows` / `mac` /
  `linux`) in `games.platforms[]`

### Requirement: Review ingestion

The collector SHALL pull English-language reviews from
`store.steampowered.com/appreviews` (sorted by recency) and write them to `signals`
with `source = 'steam_review'`.

#### Scenario: A review becomes a signal

- **WHEN** a review is fetched
- **THEN** the collector SHALL write a `signals` row with `source='steam_review'`,
  `source_id` (=`recommendationid`), `text_raw`, `author`, `timestamp`
  (=`timestamp_created`), and `game_ref`
- **AND** SHALL store `score` from `votes_up` (helpful votes; 0 when absent)

#### Scenario: Only English reviews are ingested

- **WHEN** reviews are requested with `language=english`
- **THEN** non-English reviews SHALL NOT be written to `signals`

#### Scenario: Review is linked to the catalog

- **WHEN** a review is stored
- **THEN** `game_ref` SHALL reference the matching `games.steam_app_id`

### Requirement: Incremental collection

The collector SHALL collect incrementally: review ingestion SHALL use a
`timestamp_created` watermark (not Steam's opaque cursor), and discovery SHALL
re-scan the sliding window each run without duplicating already-admitted games.

#### Scenario: Only new reviews are fetched

- **WHEN** the collector re-runs
- **THEN** it SHALL request `filter=recent` and stop at the first review whose
  `timestamp_created` is at or before the persisted watermark
- **AND** SHALL NOT re-insert previously stored reviews

#### Scenario: Already-admitted games are not re-discovered

- **WHEN** a game is already present in the catalog by `steam_app_id`
- **THEN** discovery SHALL NOT create a duplicate row (idempotent upsert)

### Requirement: Rate limiting

The collector SHALL throttle its requests to Steam to respect rate limits, with
per-endpoint budgets, and SHALL back off with jitter and retry on rate-limit (429)
and transient server (5xx) errors.

#### Scenario: Rate limits are respected

- **WHEN** the collector issues requests to Steam
- **THEN** it SHALL NOT exceed the configured per-endpoint budget (default
  `appdetails` lower than the shared 200 req / 5 min ceiling)
- **AND** SHALL retry 429/5xx with exponential backoff, jitter, a cap, and a max
  retry count

#### Scenario: Retries exhausted

- **WHEN** retries are exhausted
- **THEN** the run SHALL fail gracefully with consistent state (no partial writes)

### Requirement: Collector state

The collector SHALL persist its state in a `collector_state` table: the last
discovery run timestamp, per-game review watermarks, and the deferred `appid` set.

#### Scenario: State survives restarts

- **WHEN** the collector restarts
- **THEN** it SHALL resume from persisted state rather than re-scanning from scratch

#### Scenario: State is upserted and pruned

- **WHEN** state is written
- **THEN** it SHALL upsert on the state key (`INSERT … ON CONFLICT (key) DO UPDATE`)
- **AND** deferred entries whose `release_date` has aged out of the window SHALL be
  pruned
