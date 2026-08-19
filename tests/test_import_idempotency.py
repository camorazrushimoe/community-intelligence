"""Integration tests for idempotent import and DB-backed mention resolution."""

from datetime import date
from decimal import Decimal

from catalog.import_catalog import import_catalog
from catalog.matching import resolve_mention
from catalog.models import Game
from catalog.seed import SEED_GAMES

_TEST_APP_ID = 987654321


def _test_game(name: str, *variants: str) -> Game:
    return Game(
        steam_app_id=_TEST_APP_ID,
        name=name,
        name_variants=list(variants),
        genres=["Action"],
        tags=["test"],
        developer="Test Dev",
        publisher="Test Pub",
        release_date=date(2020, 1, 1),
        price=Decimal("9.99"),
        platforms=["PC"],
    )


def test_reimport_does_not_duplicate(db_connection):
    first = _test_game("Reimport Test", "RT")
    second = _test_game("Reimport Test Updated", "RT", "RTU")

    try:
        with db_connection.cursor() as cur:
            cur.execute("DELETE FROM games WHERE steam_app_id = %s", (_TEST_APP_ID,))

        import_catalog(db_connection, [first])
        import_catalog(db_connection, [second])

        with db_connection.cursor() as cur:
            cur.execute(
                "SELECT count(*), max(name) FROM games WHERE steam_app_id = %s",
                (_TEST_APP_ID,),
            )
            count, name = cur.fetchone()
            assert count == 1
            assert name == "Reimport Test Updated"  # updated, not duplicated
    finally:
        with db_connection.cursor() as cur:
            cur.execute("DELETE FROM games WHERE steam_app_id = %s", (_TEST_APP_ID,))


def test_resolve_mention_against_db(db_connection):
    rdr2 = next(g for g in SEED_GAMES if g.steam_app_id == 1174180)
    import_catalog(db_connection, [rdr2])

    hit = resolve_mention("RDR2", db_connection)
    assert hit.resolved is True
    assert hit.steam_app_id == 1174180

    miss = resolve_mention("Totally Unknown Game XYZ", db_connection)
    assert miss.resolved is False
    assert miss.steam_app_id is None
