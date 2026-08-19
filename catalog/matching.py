"""Deterministic name matching: normalize a mention and resolve it to a game.

v1 strategy (no embeddings yet): normalize the incoming mention (lowercase,
trim, strip punctuation/emoji), then exact-match it against a game's canonical
`name` and every entry in `name_variants[]`. Unmatched mentions are returned as
an unresolved result — never silently dropped. Semantic/embedding matching is a
later enhancement.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

from catalog.models import Game

# Anything that is not a letter/digit/whitespace is removed: punctuation,
# symbols, emoji, and underscores. NFKC first folds full-width/compatibility
# forms so, e.g., "ﬁ" and emoji variants collapse toward ASCII where possible.
_PUNCT_RE = re.compile(r"[^\w\s]|_", re.UNICODE)
_WS_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Normalize a mention or catalog name into a comparable token.

    Lowercases, trims, strips punctuation/emoji, and collapses internal
    whitespace. Deterministic and cheap — no embeddings.
    """
    if not text:
        return ""
    folded = unicodedata.normalize("NFKC", text)
    no_punct = _PUNCT_RE.sub("", folded)
    return _WS_RE.sub(" ", no_punct).strip().lower()


@dataclass(frozen=True)
class GameMatch:
    """Outcome of resolving a mention against the catalog.

    On a hit, `resolved` is True and `steam_app_id` links the mention to its
    game. On a miss, `resolved` is False and `steam_app_id` is None — the caller
    is expected to flag the mention for later review.
    """

    steam_app_id: int | None
    resolved: bool
    matched_name: str | None = None
    matched_via: str | None = None  # "name" | "variant"


_UNMATCHED = GameMatch(steam_app_id=None, resolved=False)


def find_game(mention: str, games: Iterable[Game]) -> GameMatch:
    """Resolve a mention to a catalog entry by exact normalized name/variant match.

    Returns a `GameMatch` carrying the matched `steam_app_id`, or an unresolved
    result when nothing matches.
    """
    needle = normalize(mention)
    if not needle:
        return _UNMATCHED

    for game in games:
        if normalize(game.name) == needle:
            return GameMatch(game.steam_app_id, True, game.name, "name")
        for variant in game.name_variants:
            if normalize(variant) == needle:
                return GameMatch(game.steam_app_id, True, game.name, "variant")

    return _UNMATCHED


def resolve_mention(mention: str, conn) -> GameMatch:
    """Resolve a mention against the catalog stored in PostgreSQL.

    Loads `steam_app_id`, `name` and `name_variants[]` and delegates to the pure
    `find_game` matcher. Fine for the v1 seed scale (10-20 games); a larger
    catalog would push the matching into SQL or an index.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT steam_app_id, name, name_variants FROM games")
        rows = cur.fetchall()

    games = [
        Game(steam_app_id=r[0], name=r[1], name_variants=list(r[2] or []))
        for r in rows
    ]
    return find_game(mention, games)
