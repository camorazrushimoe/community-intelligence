## 1. Database schema

- [x] 1.1 Add migration creating table `games` (`steam_app_id` int PK, `name` text NOT NULL, `name_variants` text[], `genres` text[], `tags` text[], `developer` text, `publisher` text, `release_date` date, `price` numeric, `platforms` text[])
- [x] 1.2 Add upsert path on `steam_app_id` (`INSERT ... ON CONFLICT (steam_app_id) DO UPDATE`)

## 2. Catalog seed

- [x] 2.1 Provide a seed of 10–20 games (single genre) with `name` + `name_variants[]`

## 3. Name matching

- [x] 3.1 Normalize input: lowercase, trim, strip punctuation/emoji
- [x] 3.2 Match a mention against `name` and every `name_variants[]` entry
- [x] 3.3 Return the matched `steam_app_id`; on no match return `null` and flag `unmatched`

## 4. Tests

- [x] 4.1 Unit test: alias "RDR2" resolves to "Red Dead Redemption 2"
- [x] 4.2 Unit test: unknown mention returns unresolved (not silently dropped)
- [x] 4.3 Unit test: re-import of an existing `steam_app_id` does not duplicate the row
