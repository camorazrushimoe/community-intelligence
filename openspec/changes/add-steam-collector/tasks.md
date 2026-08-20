## 1. Signals schema

- [ ] 1.1 Add migration creating `signals` (id uuid PK, source, source_id, source_url, game_ref int FK→games, author, timestamp timestamptz, text_raw, text_clean, sentiment real, topics text[], score int, lang)
- [ ] 1.2 Enforce `UNIQUE (source, source_id)`
- [ ] 1.3 Add `game_ref` foreign key → `games.steam_app_id`
- [ ] 1.4 Relax the single-statement migration constraint in `catalog/migrate.py` (multi-statement files)

## 2. Discovery

- [ ] 2.1 Fetch candidate app ids from `IStoreService/GetAppList` (API key), filter by `last_modified`
- [ ] 2.2 Verify each candidate via `appdetails` (`release_date.coming_soon` + `release_date.date`)
- [ ] 2.3 Detect Early Access via `genres` containing `"Early Access"` (use `release_date.date`)
- [ ] 2.4 Re-scan the 30-day sliding window (inclusive, UTC) on every run
- [ ] 2.5 Persist gate-failing candidates in `steam.deferred` and re-evaluate each run while in window
- [ ] 2.6 Cache the GetAppList snapshot across runs; verify `last_modified` freshness (fallback: storefront search)

## 3. Quality gate (entry only)

- [ ] 3.1 Read `query_summary` from `appreviews` (`total_reviews`, `review_score_desc`)
- [ ] 3.2 Admit only when `total_reviews >= 50` AND score not worse than `"Mixed"` (inclusive boundaries)
- [ ] 3.3 Evaluate gate before the `games` upsert
- [ ] 3.4 Apply gate at admission only — never re-evaluate after admission

## 4. Catalog enrichment

- [ ] 4.1 Upsert `games` from `appdetails`: `name`, `genres`, `developer`, `publisher`, `release_date`, `price`, `platforms` (`cc=us`)
- [ ] 4.2 Store `price` as integer cents; free games (no `price_overview`) → `0`
- [ ] 4.3 Map `platforms.{windows,mac,linux}` booleans → canonical `text[]` labels
- [ ] 4.4 Batch `appdetails` calls (comma-separated, ~50–100 per call)
- [ ] 4.5 Leave `tags` empty (not available from `appdetails`)

## 5. Review ingestion

- [ ] 5.1 Fetch `appreviews/<appid>?json=1&language=english&filter=recent&purchase_type=all`
- [ ] 5.2 Page via cursor; stop at the first review with `timestamp_created <= watermark`
- [ ] 5.3 Map to `signals` (`source='steam_review'`, `source_id`=recommendationid, `text_raw`, `author`, `timestamp`, `score`=votes_up, `game_ref`, `lang`)
- [ ] 5.4 Persist `steam.review_watermark.<appid>` = max `timestamp_created` seen

## 6. Incremental state

- [ ] 6.1 Add migration creating `collector_state` (key/value + updated_at)
- [ ] 6.2 Upsert state (`INSERT … ON CONFLICT (key) DO UPDATE`)
- [ ] 6.3 Persist `steam.last_discovery_run`
- [ ] 6.4 Persist `steam.deferred` (appid + release_date) and prune aged-out entries

## 7. Rate limiting & run model

- [ ] 7.1 Per-endpoint throttle (`appdetails` sub-ceiling below the 200/5min shared ceiling)
- [ ] 7.2 Exponential backoff + jitter + cap + max retries on 429/5xx; fail gracefully on exhaustion
- [ ] 7.3 Acquire a Postgres advisory lock at run start (single-flight guard)
- [ ] 7.4 Provide a single CLI/cron entrypoint that runs discover → gate → enrich → ingest and exits

## 8. Test seams

- [ ] 8.1 Injectable clock (freezegun) for window/watermark/backoff boundary tests
- [ ] 8.2 HTTP mock/fixture layer with representative Steam fixtures (EA, free game, missing fields, coming_soon, 429/5xx/401/404, empty sets, multi-page reviews)
- [ ] 8.3 Deterministic `release_date.date` parsing (explicit format + UTC)

## 9. Tests

### Discovery
- [ ] 9.1 D1 — release exactly at `now − 30d` → admitted (boundary)
- [ ] 9.2 D2 — `coming_soon=true` → excluded
- [ ] 9.3 D3 — `last_modified` in window but `release_date` older → excluded
- [ ] 9.4 D4 — EA genre + `release_date.date` → discovered with that date
- [ ] 9.5 D5 — `appdetails` missing `release_date` block → handled, no crash
- [ ] 9.6 D6 — invalid appid / `appdetails` error → run continues, error logged

### Quality gate
- [ ] 9.7 G1 — `total_reviews == 50`, score `Mixed` → admitted (boundary)
- [ ] 9.8 G2 — `total_reviews == 49`, score `Positive` → rejected
- [ ] 9.9 G3 — `total_reviews == 100`, score `Mostly Negative` → rejected
- [ ] 9.10 G4 — 30 reviews day 1 (reject) → 60 reviews day 10 (admit)
- [ ] 9.11 G5 — admitted game decays Very Positive → Overwhelmingly Negative → still collected
- [ ] 9.12 G6 — admitted game's review count drops below 50 → still collected
- [ ] 9.13 G7 — missing `query_summary` / `total_reviews=0` → rejected, no crash

### Enrichment
- [ ] 9.14 E1 — full metadata upsert keyed by `steam_app_id`
- [ ] 9.15 E2 — free game (no `price_overview`) → `price=0`, no error
- [ ] 9.16 E3 — empty `tags` / missing `platforms` → stored per contract
- [ ] 9.17 E4 — re-sync changed price/name → row updated, no duplicate

### Review ingestion
- [ ] 9.18 R1 — review → `signals` row with all fields mapped
- [ ] 9.19 R2 — `votes_up=0`/absent → `score=0`
- [ ] 9.20 R3 — non-English review → excluded
- [ ] 9.21 R4 — same `recommendationid` re-fetched → no duplicate `signals` row
- [ ] 9.22 R5 — empty review text → stored/skipped per contract
- [ ] 9.23 R6 — multi-page reviews ingested; loop terminates on empty page

### Incremental / state
- [ ] 9.24 I1 — re-run with same watermark → 0 new reviews inserted
- [ ] 9.25 I2 — restart from persisted watermark → resumes, no re-insertion
- [ ] 9.26 I3 — game already in catalog → discovery does not duplicate `games` row
- [ ] 9.27 I4 — fresh run with empty `collector_state` → seeds state correctly
- [ ] 9.28 I5 — deferred candidate re-evaluated while in window

### Rate limiting
- [ ] 9.29 L1 — N requests → never exceeds per-endpoint budget (inject clock)
- [ ] 9.30 L2 — 429 → backoff then retry succeeds
- [ ] 9.31 L3 — 5xx → backoff + retry
- [ ] 9.32 L4 — retries exhausted → fail gracefully, consistent state
- [ ] 9.33 L5 — discovery + ingestion share budget correctly (no double-count)
