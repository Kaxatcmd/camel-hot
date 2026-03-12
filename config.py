"""
Configuration module for DJ Harmonic Analyzer.

Centralizes all configurable parameters, paths, and settings.
This module replaces hardcoded values across the application.

Usage:
    from config import AUDIO_LOAD_DURATION_LONG, get_assets_dir
    
    # Get any config value
    duration = AUDIO_LOAD_DURATION_LONG
    assets = get_assets_dir()
"""

import os
from pathlib import Path

# ─── BASE PATHS ───────────────────────────────────────────────────────
# Handle both normal and frozen (PyInstaller/Nuitka) environments
if getattr(os, "frozen", False):
    # Running as compiled executable (PyInstaller/Nuitka)
    BASE_DIR = Path(os.sys._MEIPASS) if hasattr(os.sys, "_MEIPASS") else Path(sys.executable).parent
else:
    # Running as normal Python script
    BASE_DIR = Path(__file__).resolve().parent

PROJECT_ROOT = BASE_DIR
"""Project root directory."""

ASSETS_DIR = PROJECT_ROOT / "assets"
"""Assets directory (images, icons, etc.)."""

INPUT_AUDIO_DIR = PROJECT_ROOT / "input_audio"
"""Input audio directory for batch processing."""

OUTPUT_AUDIO_DIR = PROJECT_ROOT / "output_audio"
"""Output directory for organized files."""

LOGS_DIR = PROJECT_ROOT / "logs"
"""Logs directory."""

DOCS_DIR = PROJECT_ROOT / "docs"
"""Documentation directory."""

DATA_DIR = PROJECT_ROOT / "data"
"""Data directory for runtime data files."""


# ─── AUDIO ANALYSIS PARAMETERS ─────────────────────────────────────
"""Duration (seconds) for key detection analysis."""
AUDIO_LOAD_DURATION_SHORT = 30

"""Duration (seconds) for full track analysis (key + BPM + advanced features)."""
AUDIO_LOAD_DURATION_LONG = 60

"""librosa peak picking parameters for onset detection."""
PEAK_PICK_PARAMS = {
    "pre_max": 3,
    "post_max": 3,
    "pre_avg": 3,
    "post_avg": 3,
    "delta": 0.0,
    "wait": 10,
}

"""Default kick regularity fallback value when detection fails."""
KICK_REGULARITY_FALLBACK = 0.3

"""Default kick regularity fallback when librosa unavailable."""
KICK_REGULARITY_NO_LIBROSA = 0.5

"""Default percussion density fallback."""
PERCUSSION_DENSITY_FALLBACK = 0.3

"""Swing classification thresholds."""
SWING_THRESHOLDS = {
    "none": 0.1,
    "light": 0.5,
    "moderate": 0.8,
    "strong": 0.9,
}

"""Dissonant interval semitone distances."""
DISSONANT_INTERVALS = [1, 6, 11]

"""Default attack steepness when detection fails."""
ATTACK_STEEPNESS_FALLBACK = 0.3


# ─── PLAYLIST & FILE ORGANIZATION ─────────────────────────────────
"""Default maximum songs in generated playlist."""
DEFAULT_PLAYLIST_LIMIT = 20

"""Supported audio file extensions."""
SUPPORTED_AUDIO_EXTENSIONS = [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aiff"]

"""Whether to move files by default (destructive) or copy (safe)."""
DEFAULT_MOVE_FILES = False


# ─── GUI THEME & COLORS ───────────────────────────────────────────
"""Main UI theme gradient colors (Desert Sunset theme)."""
THEME_GRADIENT_COLORS = {
    "dark_green": "#1a4d2e",
    "medium_green": "#3d6e40",
    "light_yellow": "#f4d03f",
    "orange": "#ff9500",
    "dark_orange": "#f07c1e",
    "burgundy": "#c1440e",
}

"""File dialog filter for audio files."""
AUDIO_FILE_FILTER = "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a *.aiff);;All Files (*)"


# ─── LOGGING CONFIGURATION ────────────────────────────────────────
"""Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""
LOG_LEVEL = "INFO"

"""Log format string."""
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

"""Log file name."""
LOG_FILE = "dj_analyzer.log"

"""Maximum size of log file before rotation (in bytes)."""
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB

"""Number of backup log files to keep."""
LOG_BACKUP_COUNT = 3


# ─── HELPER FUNCTIONS ─────────────────────────────────────────────
def get_assets_dir() -> Path:
    """Get assets directory, creating it if it doesn't exist."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    return ASSETS_DIR


def get_logs_dir() -> Path:
    """Get logs directory, creating it if it doesn't exist."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    return LOGS_DIR


def get_data_dir() -> Path:
    """Get data directory, creating it if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


def get_input_audio_dir() -> Path:
    """Get input audio directory, creating it if it doesn't exist."""
    INPUT_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    return INPUT_AUDIO_DIR


def get_output_audio_dir() -> Path:
    """Get output audio directory, creating it if it doesn't exist."""
    OUTPUT_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_AUDIO_DIR


def ensure_dirs() -> None:
    """Ensure all required directories exist."""
    for dir_path in [ASSETS_DIR, LOGS_DIR, DATA_DIR, INPUT_AUDIO_DIR, OUTPUT_AUDIO_DIR, DOCS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)
