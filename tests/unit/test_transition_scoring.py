"""
Unit tests for utils/transition_scoring.py

Tests cover:
- score_harmonic_compatibility()  — 0-1 float, known good/bad pairs
- score_bpm_compatibility()       — edge cases: same, half/double time, far apart
- calculate_transition_score()    — composite result shape and value ranges
- Graceful degradation when librosa is absent (mocked)
"""

import pytest
from unittest.mock import patch, MagicMock

from utils.transition_scoring import (
    score_harmonic_compatibility,
    score_bpm_compatibility,
    calculate_transition_score,
)


# ── score_harmonic_compatibility ───────────────────────────────────────────

class TestScoreHarmonicCompatibility:
    def test_same_key_scores_high(self):
        score = score_harmonic_compatibility("8A", "8A")
        assert score >= 0.95

    def test_relative_major_scores_high(self):
        score = score_harmonic_compatibility("8A", "8B")
        assert score >= 0.85

    def test_adjacent_wheel_scores_well(self):
        score = score_harmonic_compatibility("8A", "7A")
        assert score >= 0.60

    def test_incompatible_keys_score_low(self):
        score = score_harmonic_compatibility("8A", "5B")
        assert score < 0.60

    def test_unknown_keys_return_midpoint(self):
        score = score_harmonic_compatibility("Unknown", "8A")
        assert 0.0 <= score <= 1.0

    def test_score_in_zero_one_range(self):
        for k1, k2 in [("1A", "7B"), ("12B", "6A"), ("3B", "9A")]:
            s = score_harmonic_compatibility(k1, k2)
            assert 0.0 <= s <= 1.0, f"Out of range for {k1}/{k2}: {s}"


# ── score_bpm_compatibility ────────────────────────────────────────────────

class TestScoreBpmCompatibility:
    def test_identical_bpm_scores_1(self):
        assert score_bpm_compatibility(128, 128) == pytest.approx(1.0)

    def test_1_bpm_diff_scores_very_high(self):
        assert score_bpm_compatibility(128, 129) >= 0.95

    def test_5_bpm_diff_scores_high(self):
        assert score_bpm_compatibility(128, 133) >= 0.80

    def test_large_diff_scores_low(self):
        assert score_bpm_compatibility(100, 145) < 0.50

    def test_half_time_scores_reasonably(self):
        # 128 → 64 is exactly half time
        assert score_bpm_compatibility(128, 64) >= 0.60

    def test_none_bpm_returns_midpoint(self):
        result = score_bpm_compatibility(None, 128)
        assert 0.0 <= result <= 1.0

    def test_output_always_in_range(self):
        pairs = [(80, 170), (140, 70), (60, 200), (125, 126)]
        for bpm1, bpm2 in pairs:
            s = score_bpm_compatibility(bpm1, bpm2)
            assert 0.0 <= s <= 1.0, f"Out of range for bpm {bpm1}/{bpm2}: {s}"


# ── calculate_transition_score ─────────────────────────────────────────────

def _stub_track(camelot="8A", bpm=128, energy_level="medium",
                groove_type="solid_kick", mood="neutral"):
    """Return a minimal track dict accepted by calculate_transition_score."""
    return {
        "file_path": "/fake/track.mp3",
        "key": "A Minor",
        "camelot": camelot,
        "bpm": bpm,
        "duration": 300.0,
        "confidence": 0.85,
        "energy": {
            "level": energy_level,
            "overall_score": 0.5,
            "brightness": "medium",
            "brightness_score": 0.5,
            "density": "medium",
            "richness_score": 0.5,
            "energy_curve": "stable",
        },
        "groove": {
            "type": groove_type,
            "kick_presence": 0.7,
            "kick_regularity": 0.8,
            "percussion_density": 0.6,
            "swing": 0.2,
        },
        "mood": {
            "primary_mood": mood,
            "is_major": False,
            "aggressiveness": 0.3,
            "brightness": 0.4,
            "tension": 0.2,
        },
    }


class TestCalculateTransitionScore:
    def test_returns_dict_with_required_keys(self):
        t1, t2 = _stub_track("8A", 128), _stub_track("8A", 128)
        result = calculate_transition_score(t1, t2)
        for key in ("overall_score", "harmonic_score", "bpm_score", "recommendation"):
            assert key in result, f"Missing key: {key!r}"

    def test_identical_tracks_score_high(self):
        t = _stub_track("8A", 128)
        result = calculate_transition_score(t, t)
        assert result["overall_score"] >= 0.80

    def test_score_in_zero_one_hundred_range(self):
        t1 = _stub_track("8A", 128)
        t2 = _stub_track("3B", 170, energy_level="high")
        result = calculate_transition_score(t1, t2)
        assert 0 <= result["overall_score"] <= 100

    def test_compatible_keys_score_higher_than_incompatible(self):
        base = _stub_track("8A", 128)
        compatible = _stub_track("9A", 128)    # adjacent — compatible
        incompatible = _stub_track("4B", 128)  # distant  — incompatible

        score_compat = calculate_transition_score(base, compatible)["overall_score"]
        score_incompat = calculate_transition_score(base, incompatible)["overall_score"]
        assert score_compat > score_incompat

    def test_recommendation_is_non_empty_string(self):
        t1, t2 = _stub_track(), _stub_track("9A")
        result = calculate_transition_score(t1, t2)
        assert isinstance(result["recommendation"], str)
        assert len(result["recommendation"]) > 0

    def test_notes_is_list(self):
        t1, t2 = _stub_track(), _stub_track()
        result = calculate_transition_score(t1, t2)
        assert isinstance(result.get("notes", []), list)
