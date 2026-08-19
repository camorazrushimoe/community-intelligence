## Why

The whole system hangs off the game catalog: every signal (review, post, comment)
must be linked to a game. Without a stable `games` table and name matching, a Steam
review and a Reddit discussion about the same game can never be joined. This is the
foundation (CI-1) of the minimal backend — nothing else can be built before it.

## What Changes

- Add PostgreSQL table `games`, keyed by `steam_app_id`.
- Add `name_variants[]` for alias matching.
- Implement deterministic name matching: resolve a mention/alias to a `steam_app_id`.
- Make catalog import idempotent (no duplicate rows on re-import).
- Ship a seed of 10–20 games (one genre).

## Capabilities

### New Capabilities

- `games-catalog`: Postgres `games` schema + deterministic name matching.

## Impact

- `migrations/` — `games` table.
- `catalog/` package — matching logic (normalize → match → flag).
- `tests/` — pytest for matching and idempotency.
