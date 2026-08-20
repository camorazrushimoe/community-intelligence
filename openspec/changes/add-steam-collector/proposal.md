## Why

A catalog of 10–20 hand-seeded games gets stale fast. The real value is a
collector that *finds* what is new on its own — new releases and Early Access
launches — and only admits the ones worth watching, then keeps ingesting their
reviews forever (even as sentiment turns). This is CI-2: turn the static seed
into a live, self-refreshing catalog plus an incremental review feed.

## What Changes

- Own the shared Level-2 `signals` schema (UNIQUE source+source_id, FK game_ref) —
  previously undefined and un-owned across CI-2/CI-3/CI-4.
- Add new-release discovery via the Steam Web API (`IStoreService/GetAppList`),
  verified against `appdetails`, over a 30-day sliding window with a **persisted
  deferred set** so gate failures are truly re-tried (not lost to a stale
  `last_modified`).
- Add an entry-only quality gate (review count + score), evaluated before
  enrichment; it never removes an already-admitted game.
- Add catalog enrichment from `appdetails` (price in cents, canonical platforms;
  `tags` deferred — not available from `appdetails`).
- Add English review ingestion into `signals` via `filter=recent` +
  `timestamp_created` watermark (not Steam's opaque cursor).
- Add per-endpoint rate limiting with backoff+jitter+cap+max-retries, and a
  Postgres advisory lock for single-flight runs.
- Add a `collector_state` table for last run, per-game watermarks, and the
  deferred set.
- Run as a periodic cron script, not a long-lived service.

## Capabilities

### Modified Capabilities

- `steam-collector`: add signals ownership, discovery, entry-only quality gate,
  enrichment, watermark-based review ingestion, rate limiting, and incremental
  state.

## Impact

- `openspec/specs/steam-collector/spec.md` — expanded to 8 requirements.
- `migrations/` — `signals` and `collector_state` tables.
- `catalog/migrate.py` — relax single-statement constraint.
- `collector/` package (new) — discovery, gate, ingestion, rate limiter, state.
- `catalog/` — enrichment upsert (reuses CI-1 idempotent path).
- `.env` / `.env.example` — `STEAM_WEB_API_KEY` (already present locally; never
  committed).
- `tests/` — pytest for discovery, gate, incrementality, rate limiting, with
  injectable clock + HTTP fixtures.
