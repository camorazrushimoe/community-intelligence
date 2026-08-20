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
where the last one left off. A **Postgres advisory lock** at run start prevents two
overlapping runs from racing on state / double-writing.

## Data flow

```
Steam
  ├─ IStoreService/GetAppList (API key) ─► appid + last_modified (candidates)
  ├─ store appdetails?appids=… ───────────► release_date / genres / metadata
  └─ store appreviews/<appid>?filter=recent&cursor=… ─► query_summary (gate) + reviews

                     │  (throttled per-endpoint; backoff+jitter on 429/5xx)
                     ▼
              collector-steam (cron script, advisory-locked)
   ├─ discover:  GetAppList → filter last_modified → appdetails → release_date in
   │             sliding window → gate → upsert `games` (or persist deferred & retry)
   ├─ ingest:    appreviews → stop at timestamp_created watermark → upsert `signals`
   └─ state:     `collector_state` (last run + review watermarks + deferred set)
                     │
                     ▼
              PostgreSQL  (games + signals + collector_state)
```

## Signals schema (owned by this change)

`signals` is the shared Level-2 home for every signal (CI-2/CI-3/CI-4 all write
here). This change creates and owns it:

```sql
CREATE TABLE signals (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    source      text NOT NULL,            -- 'steam_review' | 'reddit'
    source_id   text NOT NULL,
    source_url  text,
    game_ref    int  NOT NULL REFERENCES games(steam_app_id),
    author      text,
    timestamp   timestamptz NOT NULL,
    text_raw    text NOT NULL,
    text_clean  text,
    sentiment   real,                     -- -1..+1 (CI-4)
    topics      text[] NOT NULL DEFAULT '{}',  -- (CI-4)
    score       int NOT NULL DEFAULT 0,   -- signal weight (helpful votes / upvotes)
    lang        text,
    UNIQUE (source, source_id)
);
```

`UNIQUE (source, source_id)` — not `source_id` alone — because a Reddit id and a
Steam `recommendationid` live in different namespaces. `text_clean`, `sentiment`,
`topics` are filled by CI-4 (LLM); CI-2 writes `source`, `source_id`, `text_raw`,
`author`, `timestamp`, `score`, `game_ref`, `lang`.

## Discovery source

- **Candidates (API key):** `IStoreService/GetAppList/v1` returns appid +
  `last_modified`. A `last_modified` inside the window is a cheap "something
  changed" signal — not the release date itself. **Risk:** this store-side endpoint
  is undocumented and historically flaky; the public `ISteamApps/GetAppList`
  (no key) lacks `last_modified`. Fallback: storefront search `sort_by=Released_DESC`.
  Verify `last_modified` freshness up front; if it proves unreliable, switch the
  candidate source to storefront search.
- **Verify:** `appdetails` gives the exact `release_date.coming_soon` and
  `release_date.date`; only non-`coming_soon` dates inside `[now−30d, now]`
  (inclusive, UTC) qualify. Games whose `last_modified` changed for other reasons
  fall out here (stale `release_date`).
- **Sliding window + deferred retry:** every run re-scans releases in
  `[now−30d, now]`. A candidate that fails the gate is persisted in the deferred
  set and re-evaluated on every run until its `release_date` ages out — this is what
  makes the "retry within window" guarantee real (a stale `last_modified` would
  otherwise never re-surface the candidate).

## Early Access detection

`appdetails.genres` contains the literal genre `"Early Access"`. `release_date.date`
**is** the EA launch date (there is no separate field); EA→full-release transitions
are not signalled, so we simply use `release_date.date`.

## Quality gate (entry only)

Computed from `appreviews?json=1` `query_summary`:

- `total_reviews >= MIN_REVIEWS` (default **50**), inclusive
- `review_score_desc` not worse than **"Mixed"**, inclusive

Score ordering (best → worst): `Overwhelmingly Positive`, `Very Positive`,
`Positive`, `Mostly Positive`, `Mixed`, `Mostly Negative`, `Negative`,
`Very Negative`, `Overwhelmingly Negative`. Anything below `Mixed` is rejected.

The gate runs **once, at admission**, and **before** the `games` upsert. After
admission the game is collected indefinitely; a later score drop is retained as a
signal, never a removal.

## Review ingestion (watermark, not opaque cursor)

Steam's `cursor` is an opaque pagination token, not a time watermark. To fetch
"only new reviews":

1. Request `appreviews/<appid>?json=1&language=english&filter=recent&purchase_type=all`
   (`filter=recent` sorts chronologically; the default is by helpfulness).
2. Page via `cursor` until the first review with `timestamp_created <= watermark`.
3. Persist `watermark = max(timestamp_created)` seen this run.

Mapping → `signals`:

| signals field | source |
|---|---|
| `source` | `'steam_review'` |
| `source_id` | `recommendationid` |
| `text_raw` | `review` |
| `author` | `author.personaname` |
| `timestamp` | `timestamp_created` |
| `score` | `votes_up` (0 when absent) |
| `game_ref` | `steam_app_id` |
| `lang` | `language` |

## Catalog enrichment

`appdetails?appids=<id>&cc=us&l=en` → upsert `games`: `name`, `genres`, `developer`,
`publisher`, `release_date`, `price`, `platforms`. `tags` is **not** populated
(`appdetails` exposes `genres`/`categories`, not user tags) — left empty for now;
source it later (e.g. SteamSpy). Price is `price_overview.final` integer **cents**
(USD via `cc=us`); free games have no `price_overview` → store `0`. `platforms`
booleans (`windows`/`mac`/`linux`) → only the `true` labels into `text[]`.

Batch `appdetails` calls (comma-separated appids, ~50–100 per call) to spare the
rate budget.

## Rate limiting

Per-endpoint budgets, not one global bucket: `appdetails` 429s well under a generic
200/5min. Defaults: shared ceiling 200 req / 5 min, `appdetails` sub-ceiling lower
(tune after measuring live limits). Backoff: exponential with jitter, capped, with
a max retry count; on exhaustion, the run fails gracefully (transactional per-game
writes so state stays consistent).

## Incremental state

```sql
CREATE TABLE collector_state (
  key        text PRIMARY KEY,
  value      text NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now()
);
```

- `steam.last_discovery_run` — ISO-8601 (metrics).
- `steam.review_watermark.<appid>` — last `timestamp_created` per game.
- `steam.deferred` — JSON array of deferred `appid`s + their `release_date`.
- Upsert: `INSERT … ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now()`.
- Prune deferred entries once `release_date` ages out of the window.

## Testability (test seams)

- **Injectable clock** (freezegun) for window/watermark/backoff boundary tests.
- **HTTP mock/fixture layer** (or VCR cassettes) with representative Steam
  fixtures: EA title, free game, missing fields, `coming_soon`, 429/5xx/401/404,
  empty result sets, multi-page reviews.
- Deterministic date parsing: `release_date.date` is a human string
  (`"Jul 1, 2026"`); parse with an explicit format + UTC.

## Config

| Constant | Default | Meaning |
|---|---|---|
| `MIN_REVIEWS` | 50 | entry gate: min total reviews |
| `MIN_SCORE` | Mixed | entry gate: min review score |
| `DISCOVERY_WINDOW_DAYS` | 30 | sliding discovery window |
| `RATE_LIMIT` | 200 / 5 min | shared request ceiling |
| `APPDETAILS_RATE_LIMIT` | lower | per-endpoint `appdetails` ceiling |

## Goals / Non-Goals

**Goals**
- Self-refreshing catalog via new-release / Early Access discovery (API-key path)
  with a real in-window retry guarantee (persisted deferred set).
- Own the `signals` schema (UNIQUE source+source_id, FK game_ref).
- Entry-only quality gate (≥50 reviews, ≥ Mixed), evaluated before enrichment.
- Metadata enrichment from `appdetails` (price in cents, canonical platforms).
- Incremental English review ingestion via `timestamp_created` watermark.
- Per-endpoint rate limiting + advisory lock + resumable cron runs.
- Test seams (injectable clock, HTTP fixtures).

**Non-Goals**
- `tags` enrichment (no source in `appdetails`; deferred).
- LLM signal processing (CI-4), Reddit collector (CI-3), Neo4j graph (CI-5).
- Semantic/embedding name matching (deferred).
- Genre whitelist/blacklist beyond the score+count gate (deferred).
- Long-lived server/API (cron script is sufficient for MVP).
