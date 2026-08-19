"""Catalog domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class Game:
    """A single game-catalog entry, keyed by Steam app id.

    `name` is the canonical display name; `name_variants` holds aliases used for
    deterministic mention matching (e.g. "RDR2" -> "Red Dead Redemption 2").
    """

    steam_app_id: int
    name: str
    name_variants: list[str] = field(default_factory=list)
    genres: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    developer: str | None = None
    publisher: str | None = None
    release_date: date | None = None
    price: Decimal | None = None
    platforms: list[str] = field(default_factory=list)
