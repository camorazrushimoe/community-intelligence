"""Unit tests for deterministic name matching (normalize -> match -> flag)."""

from catalog.matching import find_game, normalize
from catalog.seed import SEED_GAMES


def test_rdr2_alias_resolves_to_red_dead_redemption_2():
    result = find_game("RDR2", SEED_GAMES)

    assert result.resolved is True
    assert result.steam_app_id == 1174180
    assert result.matched_name == "Red Dead Redemption 2"
    assert result.matched_via == "variant"


def test_unknown_mention_returns_unresolved():
    result = find_game("Absolutely Made Up Game 999", SEED_GAMES)

    assert result.resolved is False
    assert result.steam_app_id is None


def test_normalize_lowercases_trims_and_strips_punctuation_and_emoji():
    assert normalize("  RDR2!!  ") == "rdr2"
    assert normalize("CS:GO") == "csgo"
    assert normalize("Red Dead Redemption 2") == "red dead redemption 2"
    assert normalize("RDR2 🎮") == "rdr2"
    assert normalize("!!") == ""


def test_canonical_name_matches_case_insensitively():
    result = find_game("red dead redemption 2", SEED_GAMES)

    assert result.resolved is True
    assert result.steam_app_id == 1174180
    assert result.matched_via == "name"


def test_variant_alias_matches_csgo():
    result = find_game("csgo", SEED_GAMES)

    assert result.resolved is True
    assert result.steam_app_id == 730
    assert result.matched_name == "Counter-Strike 2"
