"""
Unit tests for utils/camelot_map.py

Tests cover:
- CAMELOT_MAP completeness and correct values
- get_camelot_key() lookup
- get_relative_minor() / get_relative_major()
- is_compatible_keys() (harmonic compatibility rules)
- get_harmonic_mixes() (adjacent wheel positions)
- get_compatible_keys() (full compatible set)
- get_harmonic_compatibility_score() (0-100 scoring)
"""

import pytest

from utils.camelot_map import (
    CAMELOT_MAP,
    get_camelot_key,
    get_relative_minor,
    is_compatible_keys,
    get_harmonic_mixes,
    get_compatible_keys,
)

try:
    from utils.camelot_map import get_harmonic_compatibility_score
    HAS_SCORE = True
except ImportError:
    HAS_SCORE = False


# ── CAMELOT_MAP structure ──────────────────────────────────────────────────

class TestCamelotMapStructure:
    def test_map_has_24_entries(self):
        """Camelot system covers 12 major + 12 minor keys."""
        assert len(CAMELOT_MAP) == 24

    def test_all_values_are_valid_camelot_codes(self):
        valid = {f"{n}{s}" for n in range(1, 13) for s in ("A", "B")}
        for key, code in CAMELOT_MAP.items():
            assert code in valid, f"{key!r} → {code!r} is not a valid Camelot code"

    def test_all_24_camelot_positions_covered(self):
        expected = {f"{n}{s}" for n in range(1, 13) for s in ("A", "B")}
        assert set(CAMELOT_MAP.values()) == expected


# ── get_camelot_key ────────────────────────────────────────────────────────

class TestGetCamelotKey:
    @pytest.mark.parametrize("key_name,expected", [
        ("C Major",  "8B"),
        ("A Minor",  "8A"),
        ("G Major",  "9B"),
        ("E Minor",  "9A"),
        ("F# Major", "2B"),
        ("D Minor",  "7A"),
        ("Bb Major", "6B"),
        ("G# Minor", "1A"),
    ])
    def test_known_keys(self, key_name, expected):
        assert get_camelot_key(key_name) == expected

    def test_unknown_key_returns_none_or_unknown(self):
        result = get_camelot_key("X Dorian")
        assert result is None or result == "Unknown"


# ── Relative minor / major ─────────────────────────────────────────────────

class TestRelativeKeys:
    @pytest.mark.parametrize("camelot,expected_relative", [
        ("8B", "8A"),   # C Major ↔ A Minor
        ("8A", "8B"),
        ("9B", "9A"),   # G Major ↔ E Minor
        ("9A", "9B"),
        ("1B", "1A"),
        ("12B", "12A"),
    ])
    def test_get_relative_minor(self, camelot, expected_relative):
        result = get_relative_minor(camelot)
        assert result == expected_relative, (
            f"get_relative_minor({camelot!r}) → {result!r}, expected {expected_relative!r}"
        )


# ── is_compatible_keys ─────────────────────────────────────────────────────

class TestIsCompatibleKeys:
    @pytest.mark.parametrize("k1,k2", [
        ("8A", "8A"),   # same key
        ("8A", "8B"),   # relative major
        ("8A", "7A"),   # -1 on wheel
        ("8A", "9A"),   # +1 on wheel
        ("8B", "7B"),
        ("8B", "9B"),
        ("8B", "8A"),
        ("1A", "12A"),  # wraparound: -1 from 1 is 12
        ("1A", "2A"),
        ("12B", "1B"),  # wraparound from 12 → 1
    ])
    def test_compatible_pairs(self, k1, k2):
        assert is_compatible_keys(k1, k2) is True, f"Expected {k1}+{k2} to be compatible"

    @pytest.mark.parametrize("k1,k2", [
        ("8A", "5B"),
        ("8A", "3A"),
        ("8B", "4A"),
        ("1A", "6B"),
    ])
    def test_incompatible_pairs(self, k1, k2):
        assert is_compatible_keys(k1, k2) is False, f"Expected {k1}+{k2} to be incompatible"

    def test_unknown_key_does_not_raise(self):
        result = is_compatible_keys("Unknown", "8A")
        assert isinstance(result, bool)


# ── get_harmonic_mixes ─────────────────────────────────────────────────────

class TestGetHarmonicMixes:
    def test_returns_list_or_set(self):
        result = get_harmonic_mixes("8A")
        assert hasattr(result, "__iter__")

    def test_includes_self_and_neighbors(self):
        mixes = set(get_harmonic_mixes("8A"))
        assert "8A" in mixes
        assert "7A" in mixes
        assert "9A" in mixes

    def test_minimum_4_entries(self):
        # same, relative, -1, +1 (at minimum)
        assert len(get_harmonic_mixes("8A")) >= 4

    def test_wraparound_includes_12_from_1(self):
        mixes = set(get_harmonic_mixes("1A"))
        assert "12A" in mixes, "Wheel should wrap: 1A - 1 = 12A"

    def test_wraparound_includes_1_from_12(self):
        mixes = set(get_harmonic_mixes("12A"))
        assert "1A" in mixes, "Wheel should wrap: 12A + 1 = 1A"


# ── get_compatible_keys ────────────────────────────────────────────────────

class TestGetCompatibleKeys:
    def test_returns_iterable(self):
        result = get_compatible_keys("8A")
        assert hasattr(result, "__iter__")

    def test_consistent_with_is_compatible(self):
        compatible = set(get_compatible_keys("8B"))
        for code in compatible:
            assert is_compatible_keys("8B", code), (
                f"{code} returned by get_compatible_keys but is_compatible_keys says False"
            )


# ── get_harmonic_compatibility_score ──────────────────────────────────────

@pytest.mark.skipif(not HAS_SCORE, reason="get_harmonic_compatibility_score not available")
class TestHarmonicCompatibilityScore:
    def test_perfect_match_scores_100(self):
        result = get_harmonic_compatibility_score("8A", "8A")
        assert result["score"] == 100

    def test_relative_major_scores_high(self):
        result = get_harmonic_compatibility_score("8A", "8B")
        assert result["score"] >= 90

    def test_adjacent_scores_high(self):
        result = get_harmonic_compatibility_score("8A", "7A")
        assert result["score"] >= 75

    def test_distant_keys_score_low(self):
        result = get_harmonic_compatibility_score("8A", "5B")
        assert result["score"] < 50

    def test_returns_dict_with_score_key(self):
        result = get_harmonic_compatibility_score("8A", "9A")
        assert "score" in result
        assert 0 <= result["score"] <= 100
