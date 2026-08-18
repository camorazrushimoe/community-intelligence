# Steam Collector

## ADDED Requirements

### Requirement: Game catalog sync

The `collector-steam` service SHALL pull the game catalog from Steam (storefront API
/ SteamSpy) into the `games` table.

#### Scenario: Catalog is fetched and stored

- **WHEN** the collector runs
- **THEN** it SHALL upsert games into `games` keyed by `steam_app_id`
- **AND** SHALL populate `name`, `genres`, `tags`, `developer`, `publisher`,
  `release_date`, `price`, `platforms` where available

### Requirement: Review ingestion

The `collector-steam` service SHALL pull reviews from
`store.steampowered.com/appreviews` and write them to `signals` with
`source = 'steam_review'`.

#### Scenario: A review becomes a signal

- **WHEN** a review is fetched
- **THEN** the collector SHALL write a `signals` row with `source='steam_review'`,
  `source_id`, `text_raw`, `author`, `timestamp`, and `game_ref`
- **AND** SHALL preserve `score` from helpful-votes where available

#### Scenario: Review is linked to the catalog

- **WHEN** a review is stored
- **THEN** `game_ref` SHALL reference the matching `games.steam_app_id`

### Requirement: Incremental collection

The collector SHALL support incremental fetching so re-runs do not re-import the
whole history.

#### Scenario: Only new reviews are fetched

- **WHEN** the collector re-runs
- **THEN** it SHALL fetch only reviews newer than the last seen `source_id`/cursor
- **AND** SHALL NOT re-insert previously stored reviews
