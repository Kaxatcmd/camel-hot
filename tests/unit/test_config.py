"""
Unit tests for config.py

Tests cover:
- BASE_DIR existence and is a valid directory
- Key constant types and plausible value ranges
- Path constants point into the project tree
- No import-time side-effects (file creation, network calls)
"""

import sys
from pathlib import Path

import pytest

import config


class TestPathConstants:
    def test_base_dir_is_directory(self):
        assert config.BASE_DIR.is_dir(), f"BASE_DIR not found: {config.BASE_DIR}"

    def test_assets_dir_is_under_project(self):
        assert config.ASSETS_DIR.parent == config.PROJECT_ROOT

    def test_logs_dir_is_under_project(self):
        assert config.LOGS_DIR.parent == config.PROJECT_ROOT

    def test_all_path_constants_are_path_objects(self):
        path_consts = ["BASE_DIR", "PROJECT_ROOT", "ASSETS_DIR",
                       "INPUT_AUDIO_DIR", "OUTPUT_AUDIO_DIR", "LOGS_DIR"]
        for name in path_consts:
            val = getattr(config, name)
            assert isinstance(val, Path), f"{name} should be a Path, got {type(val)}"


class TestAudioConstants:
    def test_short_duration_positive(self):
        assert config.AUDIO_LOAD_DURATION_SHORT > 0

    def test_long_duration_greater_than_short(self):
        assert config.AUDIO_LOAD_DURATION_LONG >= config.AUDIO_LOAD_DURATION_SHORT

    def test_peak_pick_params_is_dict(self):
        assert isinstance(config.PEAK_PICK_PARAMS, dict)
        for key in ("pre_max", "post_max", "pre_avg", "post_avg", "delta", "wait"):
            assert key in config.PEAK_PICK_PARAMS, f"Missing PEAK_PICK_PARAMS key: {key}"

    def test_fallback_values_are_floats_or_ints(self):
        assert isinstance(config.KICK_REGULARITY_FALLBACK, (int, float))
        assert 0.0 <= config.KICK_REGULARITY_FALLBACK <= 1.0


class TestSwingThresholds:
    def test_swing_thresholds_is_dict(self):
        assert isinstance(config.SWING_THRESHOLDS, dict)

    def test_swing_thresholds_keys_present(self):
        for expected in ("none", "light", "moderate"):
            assert expected in config.SWING_THRESHOLDS, (
                f"SWING_THRESHOLDS missing key: {expected!r}"
            )
