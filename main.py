"""
DJ Harmonic Analyzer - Main Entry Point (GUI Version)

This is the main program with Graphical User Interface.
The application provides an easy-to-use GUI for:
- Analyzing music files to detect keys and BPM
- Organizing your music library by Camelot notation
- Creating harmonic mixing playlists
- Checking musical key compatibility

To run:
    python main.py

This will launch the GUI application.
"""

import logging_config
from gui.main_window import main

# Initialize logging system
logging_config.setup_logging()

if __name__ == "__main__":
    main()


