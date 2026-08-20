## Why

A catalog of 10–20 hand-seeded games gets stale fast. The real value is a
collector that *finds* what is new on its own — new releases and Early Access
launches — and only admits the ones worth watching, then keeps ingesting their
reviews forever (even as sentiment turns). This is CI-2: turn the static seed
into a live, self-refreshing catalog plus an incremental review feed.

## What Changes

- Add new-release discovery via the Steam Web API (`IStoreService/GetAppList`),
  verified against `appdetails`, over a 30-day sliding window with in-window retry.
- Add an entry-only quality gate (review count + score) so we don't ingest noise;
  it never removes an already-admitted game.
- Add catalog enrichment from `appdetails` (metadata for each known app id).
- Add English review ingestion from `appreviews` into `signals`
  (`source=steam_review`).
- Add rate limiting (≤200 req / 5 min, backoff on 429/5xx).
- Add a `collector_state` table for the last run timestamp, per-game review
  cursors, and last-checked markers.
- Run as a periodic cron script, not a long-lived service.

## Capabilities

### Modified Capabilities

- `steam-collector`: add discovery, entry-only quality gate, enrichment, review
  ingestion, rate limiting, and incremental state (the existing catalog-sync
  requirement is absorbed into discovery + enrichment).

## Impact

- `openspec/specs/steam-collector/spec.md` — expanded requirements.
- `migrations/` — `collector_state` table.
- `collector/` package (new) — discovery, gate, ingestion, rate limiter, state.
- `catalog/` — enrichment upsert (reuses CI-1 idempotent path).
- `.env` / `.env.example` — `STEAM_WEB_API_KEY` (already present locally; never
  committed).
- `tests/` — pytest for discovery, gate, incrementality, rate limiting.
