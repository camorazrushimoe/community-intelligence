"""Game catalog: schema-backed lookup + deterministic name matching (CI-1).

Public interface: resolve mentions via :func:`find_game` / :func:`resolve_mention`,
import games idempotently via :func:`import_catalog`, and manage the schema with
``python -m catalog.migrate``. Seed data lives in :mod:`catalog.seed`.
"""

from catalog.db import connect, get_connection
from catalog.import_catalog import import_catalog, upsert_game
from catalog.matching import GameMatch, find_game, normalize, resolve_mention
from catalog.models import Game

__all__ = [
    "Game",
    "GameMatch",
    "connect",
    "find_game",
    "get_connection",
    "import_catalog",
    "normalize",
    "resolve_mention",
    "upsert_game",
]
