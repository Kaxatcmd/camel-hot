"""
Shared pytest fixtures for the Camel-Hot test suite.

Fixtures are automatically discovered by pytest — import them in any test
file simply by declaring them as function arguments.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest


# ── Audio file fixtures ────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def input_audio_dir() -> Path:
    """Return the path to the sample input_audio directory.

    Tests decorated with ``@pytest.mark.integration`` use this fixture.
    The test is skipped automatically when the directory is empty.
    """
    path = Path(__file__).resolve().parents[1] / "input_audio"
    return path


@pytest.fixture(scope="session")
def first_audio_file(input_audio_dir: Path):
    """Return the first MP3/WAV/FLAC found in input_audio/, or skip."""
    extensions = {".mp3", ".wav", ".flac", ".ogg", ".aac", ".m4a"}
    for f in sorted(input_audio_dir.iterdir()):
        if f.suffix.lower() in extensions:
            return f
    pytest.skip("No audio files found in input_audio/ — skipping integration test")


# ── Temporary directory fixtures ───────────────────────────────────────────

@pytest.fixture
def tmp_input(tmp_path: Path) -> Path:
    """A temporary directory that acts as an input folder (initially empty)."""
    d = tmp_path / "input"
    d.mkdir()
    return d


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    """A temporary directory that acts as an output folder."""
    d = tmp_path / "output"
    d.mkdir()
    return d


@pytest.fixture
def tmp_input_with_stubs(tmp_input: Path) -> Path:
    """tmp_input pre-populated with zero-byte stub files for each extension."""
    for ext in ("song_a.mp3", "track_b.wav", "mix_c.flac", "not_audio.txt"):
        (tmp_input / ext).touch()
    return tmp_input
