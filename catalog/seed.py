"""Seed catalog: 15 action games with canonical names + matching aliases.

Single genre ("Action") per the CI-1 MVP scope. Steam app ids are Steam's real
ids so the catalog can later bridge Steam reviews and Reddit mentions.
"""

from __future__ import annotations

import argparse
from datetime import date
from decimal import Decimal

from catalog.db import connect
from catalog.import_catalog import import_catalog
from catalog.models import Game


def _g(
    app_id: int,
    name: str,
    *variants: str,
    developer: str | None = None,
    publisher: str | None = None,
    released: str | None = None,
    price: str | None = None,
    tags: tuple[str, ...] = (),
    platforms: tuple[str, ...] = ("PC",),
) -> Game:
    return Game(
        steam_app_id=app_id,
        name=name,
        name_variants=list(variants),
        genres=["Action"],
        tags=list(tags),
        developer=developer,
        publisher=publisher,
        release_date=date.fromisoformat(released) if released else None,
        price=Decimal(price) if price is not None else None,
        platforms=list(platforms),
    )


SEED_GAMES: list[Game] = [
    _g(
        1174180,
        "Red Dead Redemption 2",
        "RDR2", "RDR 2", "Red Dead 2",
        developer="Rockstar Games",
        publisher="Rockstar Games",
        released="2019-12-05",
        price="59.99",
        tags=("open world", "western", "story rich", "singleplayer"),
    ),
    _g(
        730,
        "Counter-Strike 2",
        "CS2", "CS:GO", "CSGO", "csgo", "Counter-Strike", "Counter Strike",
        developer="Valve",
        publisher="Valve",
        released="2012-08-21",
        price="0.00",
        tags=("fps", "competitive", "multiplayer", "esports"),
    ),
    _g(
        271590,
        "Grand Theft Auto V",
        "GTA5", "GTA V", "GTA 5", "GTAV", "GTA",
        developer="Rockstar North",
        publisher="Rockstar Games",
        released="2015-04-14",
        price="29.99",
        tags=("open world", "crime", "multiplayer", "action"),
    ),
    _g(
        1245620,
        "Elden Ring",
        "ER",
        developer="FromSoftware",
        publisher="Bandai Namco Entertainment",
        released="2022-02-25",
        price="59.99",
        tags=("souls-like", "open world", "dark fantasy", "difficult"),
    ),
    _g(
        1091500,
        "Cyberpunk 2077",
        "CP2077", "Cyberpunk",
        developer="CD PROJEKT RED",
        publisher="CD PROJEKT RED",
        released="2020-12-10",
        price="59.99",
        tags=("open world", "rpg", "cyberpunk", "story rich"),
    ),
    _g(
        1593500,
        "God of War",
        "GoW", "GOW", "God of War 2018",
        developer="Santa Monica Studio",
        publisher="PlayStation PC LLC",
        released="2022-01-14",
        price="49.99",
        tags=("action", "story rich", "singleplayer", "mythology"),
    ),
    _g(
        292030,
        "The Witcher 3: Wild Hunt",
        "Witcher 3", "TW3", "The Witcher 3",
        developer="CD PROJEKT RED",
        publisher="CD PROJEKT RED",
        released="2015-05-18",
        price="39.99",
        tags=("open world", "rpg", "story rich", "fantasy"),
    ),
    _g(
        1151640,
        "Horizon Zero Dawn",
        "HZD", "Horizon",
        developer="Guerrilla Games",
        publisher="PlayStation PC LLC",
        released="2020-08-07",
        price="49.99",
        tags=("open world", "action", "post-apocalyptic", "singleplayer"),
    ),
    _g(
        814380,
        "Sekiro: Shadows Die Twice",
        "Sekiro",
        developer="FromSoftware",
        publisher="Activision",
        released="2019-03-22",
        price="59.99",
        tags=("souls-like", "action", "difficult", "japan"),
    ),
    _g(
        367520,
        "Hollow Knight",
        "HK",
        developer="Team Cherry",
        publisher="Team Cherry",
        released="2017-02-24",
        price="14.99",
        tags=("metroidvania", "indie", "action", "atmospheric"),
    ),
    _g(
        782330,
        "DOOM Eternal",
        "Doom Eternal", "DOOM", "Doom",
        developer="id Software",
        publisher="Bethesda Softworks",
        released="2020-03-20",
        price="39.99",
        tags=("fps", "action", "singleplayer", "gore"),
    ),
    _g(
        1145360,
        "Hades",
        developer="Supergiant Games",
        publisher="Supergiant Games",
        released="2020-09-17",
        price="24.99",
        tags=("roguelike", "indie", "action", "greek mythology"),
    ),
    _g(
        582010,
        "Monster Hunter: World",
        "MHW", "Monster Hunter World",
        developer="Capcom",
        publisher="Capcom",
        released="2018-08-09",
        price="29.99",
        tags=("action", "co-op", "multiplayer", "dragons"),
    ),
    _g(
        601150,
        "Devil May Cry 5",
        "DMC5", "DMC 5", "DMCV",
        developer="Capcom",
        publisher="Capcom",
        released="2019-03-08",
        price="39.99",
        tags=("action", "hack and slash", "stylish", "singleplayer"),
    ),
    _g(
        287700,
        "Metal Gear Solid V: The Phantom Pain",
        "MGSV", "MGS5", "MGS V", "Phantom Pain",
        developer="Kojima Productions",
        publisher="Konami Digital Entertainment",
        released="2015-09-01",
        price="19.99",
        tags=("stealth", "open world", "action", "tactical"),
    ),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the games catalog.")
    parser.add_argument(
        "--url", default=None, help="PostgreSQL URL (default: DEV_POSTGRES_URL)"
    )
    args = parser.parse_args()
    with connect(args.url, autocommit=True) as conn:
        count = import_catalog(conn, SEED_GAMES)
    print(f"upserted {count} games")


if __name__ == "__main__":
    main()
