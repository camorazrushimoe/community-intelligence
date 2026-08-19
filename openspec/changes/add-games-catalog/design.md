# Design: Game catalog (CI-1)

## Context

Every signal in the system links back to a game. The catalog is the stable backbone:
a `games` table keyed by `steam_app_id`, with `name_variants[]` used to resolve
mentions ("RDR2", "CS:GO") to a canonical game. Steam reviews already carry `app_id`,
so the catalog is also the bridge between Steam data and future Reddit mentions.

## Schema

```sql
CREATE TABLE games (
  steam_app_id  int PRIMARY KEY,
  name          text NOT NULL,
  name_variants text[] NOT NULL DEFAULT '{}',
  genres        text[] NOT NULL DEFAULT '{}',
  tags          text[] NOT NULL DEFAULT '{}',
  developer     text,
  publisher     text,
  release_date  date,
  price         numeric,
  platforms     text[] NOT NULL DEFAULT '{}'
);
```

## Name matching

Deterministic, v1 (no embeddings yet):

1. Normalize the incoming mention: lowercase, trim, strip punctuation/emoji.
2. Exact match against `name` or any `name_variants[]` entry.
3. On no match: return `null` and flag as `unmatched` — never silently dropped.
   Semantic/embedding matching is a later enhancement.

## Idempotency

Import upserts on `steam_app_id`
(`INSERT ... ON CONFLICT (steam_app_id) DO UPDATE`), so re-importing the catalog
never duplicates rows.

## Goals / Non-Goals

**Goals**
- Stable `games` table + deterministic name matching.
- Idempotent import.
- Seed of 10–20 games.

**Non-Goals**
- Semantic/embedding matching (later).
- Auto-discovery of name variants (seeded manually for now).
- Collectors — out of scope for this change.
