"""Runtime dependency checks shared by startup and packaged smoke tests."""

import importlib
import logging
import os


logger = logging.getLogger(__name__)

REQUIRED_ANALYSIS_MODULES = (
    "numpy",
    "scipy",
    "numba",
    "llvmlite",
    "soundfile",
    "audioread",
    "imageio_ffmpeg",
    "librosa",
)


def check_analysis_runtime():
    """Return import errors for packages required by audio analysis."""
    errors = []
    for module_name in REQUIRED_ANALYSIS_MODULES:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            message = f"{module_name}: {type(exc).__name__}: {exc}"
            logger.exception("Audio analysis runtime dependency failed: %s", message)
            errors.append(message)
    if not errors:
        try:
            ffmpeg_path = importlib.import_module("imageio_ffmpeg").get_ffmpeg_exe()
            if not os.path.isfile(ffmpeg_path):
                raise RuntimeError(f"Bundled ffmpeg binary not found: {ffmpeg_path}")
        except Exception as exc:
            message = f"imageio_ffmpeg binary: {type(exc).__name__}: {exc}"
            logger.exception("Audio decoder runtime dependency failed: %s", message)
            errors.append(message)
    return errors