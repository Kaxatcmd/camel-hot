"""
File Manager Package

This package handles all file-related operations:
- Finding audio files in directories
- Organizing files based on their musical properties
- Moving/copying files to appropriate locations
"""

from .organizaer import (
    find_audio_files,
    organize_by_key,
    create_playlist
)

__all__ = [
    'find_audio_files',
    'organize_by_key',
    'create_playlist'
]

