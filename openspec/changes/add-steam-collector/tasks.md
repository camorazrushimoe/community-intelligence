## 1. Discovery

- [ ] 1.1 Fetch candidate app ids from `IStoreService/GetAppList` (API key), filter by `last_modified`
- [ ] 1.2 Verify each candidate via `appdetails` (`release_date.coming_soon` + `release_date.date`)
- [ ] 1.3 Detect Early Access via `genres` containing `"Early Access"`
- [ ] 1.4 Re-scan a 30-day sliding window on every run; keep re-evaluating gate failures while inside the window
- [ ] 1.5 Cache the GetAppList snapshot across runs (avoid re-fetching ~200k appids each run)

## 2. Quality gate (entry only)

- [ ] 2.1 Read `query_summary` from `appreviews` (`total_reviews`, `review_score_desc`)
- [ ] 2.2 Admit only when `total_reviews >= 50` AND score not worse than `"Mixed"`
- [ ] 2.3 Apply gate at admission only — never re-evaluate after admission

## 3. Catalog enrichment

- [ ] 3.1 Upsert `games` metadata from `appdetails` (`name`, `genres`, `tags`, `developer`, `publisher`, `release_date`, `price`, `platforms`) with `cc=us`

## 4. Review ingestion

- [ ] 4.1 Fetch English reviews (`language=english`) from `appreviews` and map to `signals` (`source='steam_review'`, `source_id`, `text_raw`, `author`, `timestamp`, `game_ref`)
- [ ] 4.2 Preserve helpful-vote `score`

## 5. Incremental state

- [ ] 5.1 Add migration creating `collector_state` (key/value)
- [ ] 5.2 Persist `steam.last_discovery_run`
- [ ] 5.3 Persist per-game review cursor `steam.review_cursor.<appid>`
- [ ] 5.4 Persist `steam.last_checked.<appid>` for deferred candidates

## 6. Rate limiting

- [ ] 6.1 Throttle Steam requests to ≤200 / 5 min across discovery + ingestion
- [ ] 6.2 Exponential backoff + retry on 429 / 5xx

## 7. Run model

- [ ] 7.1 Provide a single CLI/cron entrypoint that runs discover → gate → enrich → ingest and exits

## 8. Tests

- [ ] 8.1 Unit test: candidate below review threshold is skipped
- [ ] 8.2 Unit test: decayed game (Very Positive → Negative) is still collected
- [ ] 8.3 Unit test: re-run does not duplicate reviews (cursor)
- [ ] 8.4 Unit test: gate-failed candidate is re-evaluated while inside the window
- [ ] 8.5 Unit test: rate limiter throttles and backs off on 429
