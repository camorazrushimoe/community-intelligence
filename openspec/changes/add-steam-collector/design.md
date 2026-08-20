# Design: Steam collector (CI-2)

## Context

The catalog (CI-1) is a hand-seeded backbone. This change makes it live: the
collector discovers new releases and Early Access launches, admits only the ones
that clear a quality bar, enriches their metadata, and keeps ingesting their
reviews incrementally — even after sentiment turns negative (that decay is exactly
the "something happened" signal the product sells).

## Run model

A **periodic script** (cron), not a long-lived server. Each run: discover →
gate → enrich → ingest, then exit. State lives in Postgres, so a fresh run resumes
where the last one left off.

## Data flow

```
Steam
  ├─ IStoreService/GetAppList (API key) ─► appid + last_modified (candidates)
  ├─ store appdetails?appids=… ───────────► release_date / genres / metadata
  └─ store appreviews/<appid>?cursor=… ───► query_summary (gate) + reviews (signals)

                     │  (throttled: ≤200 req / 5 min, backoff on 429/5xx)
                     ▼
              collector-steam (cron script)
   ├─ discover:  GetAppList → filter last_modified → appdetails → release_date in
   │             sliding window → gate → upsert `games` (or defer & retry)
   ├─ ingest:    appreviews → upsert `signals` (source='steam_review')
   └─ state:     `collector_state` (last run + review cursors + last-checked)
                     │
                     ▼
              PostgreSQL  (games + signals + collector_state)
```

## Discovery source

- **Candidates (API key):** `IStoreService/GetAppList/v1` returns every appid with
  `last_modified`. A `last_modified` inside the window is a cheap "something
  changed" signal — not the release date itself.
- **Verify:** `appdetails` gives the exact `release_date.coming_soon` and
  `release_date.date`; only non-`coming_soon` dates inside the window qualify.
  Games whose `last_modified` changed for other reasons (patches, price) fall out
  here because their `release_date` is old.
- **Sliding window:** every run re-scans releases in `[now − 30d, now]`, so a game
  that failed the gate on day 1 is re-evaluated on later runs until it ages out of
  the window. `steam.last_discovery_run` is recorded for metrics, not correctness.

## Early Access detection

`appdetails.genres` contains the literal genre `"Early Access"` for EA titles. Treat
the EA launch date as the release date.

## Quality gate (entry only)

Computed from `appreviews?json=1` `query_summary`:

- `total_reviews >= MIN_REVIEWS` (default **50**)
- `review_score` not worse than **"Mixed"**

Score ordering (best → worst): `Overwhelmingly Positive`, `Very Positive`,
`Positive`, `Mostly Positive`, `Mixed`, `Mostly Negative`, `Negative`,
`Very Negative`, `Overwhelmingly Negative`. Anything below `Mixed` is rejected.

The gate runs **once, at admission**. After admission the game is collected
indefinitely; a later score drop is retained as a signal, never a removal.

## Review ingestion

`store.steampowered.com/appreviews/<appid>?json=1&language=english&cursor=…` →
`signals`:

| signals field | source |
|---|---|
| `source` | `'steam_review'` |
| `source_id` | `recommendationid` |
| `text_raw` | `review` |
| `author` | `author.personaname` |
| `timestamp` | `timestamp_created` |
| `score` | `votes_up` (helpful votes) |
| `game_ref` | `steam_app_id` |

English only (`language=english`) to keep CI-4 (LLM) cheap and clean.

## Catalog enrichment

`appdetails?appids=<id>&cc=us&l=en` → upsert `games` (`name`, `genres`, `tags`,
`developer`, `publisher`, `release_date`, `price` via `price_overview.final`,
`platforms` from the `platforms` block). `cc=us` pins the price region.

## Rate limiting

Global token bucket: ≤200 requests / 5 minutes across discovery + ingestion.
On `429` or `5xx`, exponential backoff (e.g. 1s → 2s → 4s …) with a cap, then
resume. Long pagination loops (GetAppList over ~200k appids) are cached across
runs so the full list is not re-fetched every run.

## Incremental state

```sql
CREATE TABLE collector_state (
  key        text PRIMARY KEY,
  value      text NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);
```

- `steam.last_discovery_run` — ISO-8601 timestamp (metrics).
- `steam.review_cursor.<appid>` — last `appreviews` cursor per game.
- `steam.last_checked.<appid>` — last gate-check time; used to throttle re-checking
  of deferred candidates still inside the window.

## Config

| Constant | Default | Meaning |
|---|---|---|
| `MIN_REVIEWS` | 50 | entry gate: min total reviews |
| `MIN_SCORE` | Mixed | entry gate: min review score |
| `DISCOVERY_WINDOW_DAYS` | 30 | sliding discovery window |
| `RATE_LIMIT` | 200 / 5 min | Steam request throttle |

## Goals / Non-Goals

**Goals**
- Self-refreshing catalog via new-release / Early Access discovery (API-key path).
- Entry-only quality gate (≥50 reviews, ≥ Mixed) with in-window retry.
- Metadata enrichment from `appdetails`.
- Incremental English review ingestion with cursor state.
- Rate-limited, resumable cron runs.

**Non-Goals**
- LLM signal processing (CI-4).
- Reddit collector (CI-3).
- Neo4j graph (CI-5).
- Semantic/embedding name matching (deferred).
- Genre whitelist/blacklist beyond the score+count gate (deferred).
- Long-lived server/API (cron script is sufficient for MVP).
