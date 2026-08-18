# Community Intelligence — Architecture

> A service that collects and structures **player voice** for market intelligence in
> the video-game industry.

## 1. Idea & positioning

We collect player opinions from open communities and turn them into a structured,
time-series graph of insights. The client gets *"why are players angry / what do they
want / what is rising"* — not *"how many sold"*.

- **Clients:** game studios (live-service, indie), publishers, investors, UA/marketing agencies.
- **Differentiation vs Newzoo / Sensor Tower:** they track sales/revenue; we track the
  player voice (community signal).
- **Agent-native:** data is served both to humans (dashboard) and to AI agents
  (structured graph / API).

## 2. Architecture — two parts

```
[ Collectors ]  →  [ Storage & processing ]
  (ingestion)        (Postgres + Neo4j + API)
```

### Part A — Collectors (ingestion layer)

One service per source. Shared contract: schedule/trigger in → normalized signals out.

| Collector | Source | Pulls | Status |
|---|---|---|---|
| `collector-steam` | Steam store API + appreviews | game catalog, reviews | MVP |
| `collector-reddit` | Arctic Shift API | posts/comments mentioning games | MVP |
| `collector-discord` | (later) | community messages | roadmap |
| `collector-steamdb` | (later) | concurrent players | roadmap |

### Part B — Storage & processing

Two databases:

1. **Postgres** — reference data + raw/normalized signals (`games` L1, `signals` L2).
2. **Neo4j** — entities + edges + time series (L3).

Pipeline:

```
collector → normalization → Postgres → ETL → Neo4j → API / dashboard
```

## 3. Data model — 3 levels

### Level 1 — Game catalog (Postgres, `games`)

The stable backbone every signal attaches to.

| Field | Type | Purpose |
|---|---|---|
| `steam_app_id` | int, PK | **primary key** — bridge between Reddit and Steam |
| `name` | text | canonical name |
| `name_variants` | text[] | synonyms for matching: "CS:GO", "csgo", "Counter-Strike" |
| `genres` | text[] | genres |
| `tags` | text[] | Steam tags (for correlations) |
| `developer` | text | |
| `publisher` | text | |
| `release_date` | date | distinguish pre-release hype from post-release |
| `price` | numeric | later: price vs sentiment |
| `platforms` | text[] | PC / console / mobile |

### Level 2 — Signals (Postgres, `signals`)

One unit of player voice: a post / review / comment.

| Field | Type | Purpose |
|---|---|---|
| `id` | uuid, PK | |
| `source` | enum | `reddit` \| `steam_review` |
| `source_id` | text | id at the source |
| `source_url` | text | for verification |
| `game_ref` | int, FK→games | **link to catalog** |
| `author` | text | |
| `timestamp` | timestamptz | for the time series |
| `text_raw` | text | original |
| `text_clean` | text | cleaned |
| `sentiment` | real | −1…+1 |
| `topics` | text[] | gameplay, bugs, performance, monetization, story, ui… |
| `score` | int | upvotes / helpful votes (signal weight) |
| `lang` | text | |

### Level 3 — Insights (Neo4j, graph)

- **Nodes:** `Game`, `Topic`, `Source`, `Author`, `Event` (patch/release), `Day` (time slice).
- **Edges:**
  - `(Game)-[HAS_SIGNAL {sentiment, at}]->(Signal)`
  - `(Signal)-[ABOUT {sentiment}]->(Topic)`
  - `(Game)-[SENTIMENT_AT {score}]->(Day)` — time series
  - `(Game)-[COMPETES_WITH]->(Game)` — later, competitive links

First aggregations:

1. **Game × Day × sentiment** — sentiment trend.
2. **Game × Topic × sentiment** — what exactly players complain about.
3. **Topic × Day** — rising topics (trend detection).

## 4. Matching key

A Reddit mention is linked to a game via `steam_app_id` + `name_variants`. Without the
catalog it is impossible to tie a Steam review to a Reddit discussion.

## 5. Tech stack

- **Postgres** (+ TimescaleDB optional for time series).
- **Neo4j** for the graph.
- **Python + FastAPI** — collectors and API.
- **LLM: DeepSeek-V3** — topic extraction, sentiment, synonym generation
  (see `openspec/specs/signal-processing/spec.md`).
- Optional queue: NATS/Redis.

## 6. MVP scope

- 10–20 games in a single genre.
- 2 collectors: Steam + Reddit.
- Postgres (`games` + `signals`).
- Simplest aggregation: **30-day sentiment trend + top-5 pain topics** per game.
- Minimal JSON API, optionally a simple dashboard.

## 7. Roadmap → OpenSpec capabilities

| Roadmap | Capability (spec) |
|---|---|
| CI-1 | `openspec/specs/games-catalog/spec.md` |
| CI-2 | `openspec/specs/steam-collector/spec.md` |
| CI-3 | `openspec/specs/reddit-collector/spec.md` |
| CI-4 | `openspec/specs/signal-processing/spec.md` |
| CI-5 | `openspec/specs/knowledge-graph/spec.md` |
| CI-6 | `openspec/specs/api-dashboard/spec.md` |
