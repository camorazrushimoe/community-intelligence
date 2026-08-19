"""Idempotent catalog import: upsert games on `steam_app_id`."""

from __future__ import annotations

from collections.abc import Iterable

from catalog.models import Game

_UPSERT_SQL = """
INSERT INTO games (
    steam_app_id, name, name_variants, genres, tags,
    developer, publisher, release_date, price, platforms
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
ON CONFLICT (steam_app_id) DO UPDATE SET
    name          = EXCLUDED.name,
    name_variants = EXCLUDED.name_variants,
    genres        = EXCLUDED.genres,
    tags          = EXCLUDED.tags,
    developer     = EXCLUDED.developer,
    publisher     = EXCLUDED.publisher,
    release_date  = EXCLUDED.release_date,
    price         = EXCLUDED.price,
    platforms     = EXCLUDED.platforms
"""


def upsert_game(conn, game: Game) -> None:
    """Insert or update a single game, keyed by `steam_app_id`."""
    with conn.cursor() as cur:
        cur.execute(
            _UPSERT_SQL,
            (
                game.steam_app_id,
                game.name,
                list(game.name_variants),
                list(game.genres),
                list(game.tags),
                game.developer,
                game.publisher,
                game.release_date,
                game.price,
                list(game.platforms),
            ),
        )


def import_catalog(conn, games: Iterable[Game]) -> int:
    """Upsert a batch of games; returns the number of games processed."""
    count = 0
    for game in games:
        upsert_game(conn, game)
        count += 1
    return count
