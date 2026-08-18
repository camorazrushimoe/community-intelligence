# Reddit Collector

## ADDED Requirements

### Requirement: Mention search

The `collector-reddit` service SHALL find posts/comments that mention games from the
catalog via the Arctic Shift API.

#### Scenario: A mention is discovered and matched

- **WHEN** a post/comment mentions a game
- **THEN** the collector SHALL match it to a catalog entry via `name_variants`
- **AND** SHALL write a `signals` row with `source='reddit'`, `source_id`,
  `source_url`, `text_raw`, `author`, `timestamp`, and `game_ref`

#### Scenario: Multiple games mentioned

- **WHEN** a single post mentions more than one catalog game
- **THEN** the collector SHALL produce one `signals` row per matched game
- **AND** SHALL preserve `source_url` so each row is independently verifiable

### Requirement: Deduplication

The collector SHALL NOT write duplicate signals for the same `source_id`.

#### Scenario: Repeated fetch does not duplicate

- **WHEN** the collector re-fetches the same post/comment
- **THEN** it SHALL NOT insert a second `signals` row for the same `source_id`

### Requirement: Weight capture

The collector SHALL capture engagement as signal weight.

#### Scenario: Score is recorded

- **WHEN** a post/comment has upvotes/score available
- **THEN** the collector SHALL store it in `signals.score`
