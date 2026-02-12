"""
Audio Analysis Package

This package contains tools for analyzing audio files to detect
musical properties like tempo (BPM) and musical key.

The main goal is to help DJs understand what key a song is in,
so they can mix harmonically compatible tracks together.
"""

from .key_detection import (
    detect_key_from_audio,
    detect_bpm,
    analyze_track
)

__all__ = [
    'detect_key_from_audio',
    'detect_bpm', 
    'analyze_track'
]

