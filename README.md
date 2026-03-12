# DJ Harmonic Analyzer

A professional DJ tool for analyzing music files, detecting musical keys and tempos, and organizing your music library by harmonic compatibility.

## Features

### Core Functionality
- **Music Key Detection**: Analyzes audio files to detect musical keys using chroma-based analysis
- **BPM Detection**: Measures tempo (beats per minute) of audio tracks
- **Camelot Key Mapping**: Converts musical keys to DJ-friendly Camelot notation
- **File Organization**: Automatically sorts your music library by Camelot key
- **Playlist Generation**: Creates harmonic mixing playlists with multiple strategies:
  - Key-based filtering (harmonically compatible tracks only)
  - BPM range filtering  
  - Key-to-key transitions
  - Harmonic sequences
  - Camelot zone compatibility

### Analysis Features
- Groove/rhythm detection
- Mood classification (major/minor, aggressiveness, tension, brightness)
- Energy level analysis
- Transition scoring for seamless mixing

### User Experience
- PyQt5 graphical user interface
- Multi-language support (English, Portuguese, Spanish)
- Real-time analysis with progress indication
- Desert sunset theme
- Camelot wheel visualization
- DJ tips and recommendations

## Installation

### Requirements
- Python 3.8+
- LibreFFmpeg (for audio processing via librosa)

### Setup

```bash
# Clone or download the project
cd DJ_Harmonic_Analyzer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Project Structure

```
.
├── main.py                    # Application entry point (launches GUI)
├── config.py                  # Configuration & paths management
├── logging_config.py          # Structured logging setup
│
├── gui/
│   ├── main_window.py         # PyQt5 main GUI window
│   └── file_manager/
│       └── organizer.py       # File organization logic
│
├── audio_analysis/
│   ├── key_detection.py       # Musical key & BPM detection
│   ├── groove_analysis.py     # Rhythm analysis
│   ├── mood_classification.py # Emotional characteristics
│   └── energy_detection.py    # Energy level analysis
│
├── utils/
│   ├── camelot_map.py         # Camelot notation mapping
│   ├── transition_scoring.py  # Harmonic compatibility scoring
│   ├── translations.py        # Multi-language support
│   ├── dj_tips.py             # DJ tips & advice
│   └── camelot_wheel_generator.py  # Camelot wheel visualization
│
├── assets/                    # Images, icons, logos
├── input_audio/               # Sample audio files for testing
├── output_audio/              # Organized music output
├── docs/                      # Documentation
├── logs/                      # Application logs
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Usage

### Via GUI
Simply run the application:
```bash
python main.py
```

The GUI provides four main tabs:

1. **Analyze**: Analyze individual audio files
2. **Organize**: Batch organize your music library by key
3. **Playlists**: Generate harmonic mixing playlists
4. **Wheel**: View the Camelot wheel visualization

### Configuration
Configuration is centralized in `config.py`:
- Audio analysis parameters (duration, sensitivity)
- File paths and directories
- GUI appearance (colors, themes)
- Logging settings
- Default playlist settings

To customize, edit `config.py` before running the application.

## How It Works

### 1. Audio Analysis Pipeline
1. **Audio Loading**: Loads up to 60 seconds of audio for analysis
2. **Chroma Analysis**: Extracts pitch content to determine musical key
3. **Onset Detection**: Identifies percussive hits for BPM and groove analysis
4. **Spectral Analysis**: Analyzes frequency content for energy and brightness
5. **AI Classification**: Determines mood, groove type, and energy level

### 2. Camelot Notation
The application uses Camelot wheel notation (1-12 with A/B suffixes):
- **Numbers (1-12)**: Position on the wheel (chromatic keys)
- **A**: Major keys
- **B**: Minor keys

Compatible keys form circles on the Camelot wheel, making harmonic mixing straightforward.

### 3. File Organization
- Scans input directory recursively for audio files
- Analyzes each file to extract Camelot key
- Creates subdirectories for each key (e.g., `8A/`, `9B/`)
- Copies or moves files to matching folders (default: copy for safety)

### 4. Playlist Generation
Multiple playlist strategies available:
- **Harmonic Playlist**: Only includes compatible keys
- **Key-to-Key Transition**: Creates a path between two keys
- **Harmonic Sequence**: Follows a predefined path around the wheel
- **Camelot Zone**: Groups compatible keys in a specific region

## Supported Audio Formats

- MP3 (.mp3)
- WAV (.wav)
- FLAC (.flac)
- OGG Vorbis (.ogg)
- M4A/AAC (.m4a)
- AIFF (.aiff)

## Key Technologies

- **PyQt5**: Cross-platform GUI framework
- **Librosa**: Audio analysis and feature extraction
- **NumPy**: Numerical computing for signal processing
- **Python pathlib**: Cross-platform file handling
- **Logging**: Structured error tracking

## Logging

Application logs are saved to `logs/dj_analyzer.log` with automatic rotation. Configure logging level in `config.py`.

## Performance

- Single track analysis: ~2-5 seconds
- Playlist generation: ~1 second per track
- Full library organization: Depends on library size (typically 1-2 seconds per track)

## Cross-Platform Support

The application is designed to work on:
- **Linux** (Ubuntu, Debian, etc.)
- **macOS** (Intel and Apple Silicon)
- **Windows** (7, 10, 11+)

All file paths use cross-platform Path handling, and OS-specific code is abstracted.

## Packaging

The project is prepared for packaging with tools like:
- PyInstaller (Windows executable)
- Nuitka (compiled Python)
- cx_Freeze (cross-platform executable)

Asset loading is dynamic, and all paths are relative or configurable.

## Contributing

Contributions are welcome! Areas for enhancement:
- Additional audio analysis features
- Performance optimizations
- Additional language translations
- Advanced editing tools

## FAQ

**Q: Why didn't my file analyze correctly?**
- Ensure the audio file is valid and not corrupted
- Librosa may have issues with certain codecs (try converting to WAV)
- Check `logs/dj_analyzer.log` for error details

**Q: What's the Camelot wheel?**
- A visual representation of compatible musical keys for DJs
- Keys on adjacent positions are harmonically compatible
- The tool uses this to recommend mixing combinations

**Q: Can I organize files without moving them?**
- Yes! By default, files are copied. To move files instead, enable "Move Files" in the GUI

**Q: How accurate is the key detection?**
- Accuracy depends on audio quality and style (~85-95% for most genres)
- Live recordings and complex arrangements are more challenging
- Always review results before relying on them for mixing

## License

This project is released under the MIT License. See LICENSE file for details.

## Troubleshooting

### GUI fails to start
```bash
python -c "from gui.main_window import DJAnalyzerGUI"
```
This will show import errors if they exist.

### Audio analysis returns "Unknown"
- Check that librosa is installed: `pip list | grep librosa`
- Verify audio file is not corrupted
- Try a different audio file or format

### Performance issues
- Reduce the number of concurrent analyses
- Use shorter audio files for testing
- Check system resources (disk space, RAM)

## Additional Resources

- **Camelot Wheel Guide**: See `docs/camelot_system.md`
- **Architecture Overview**: See `docs/architecture.md`
- **Configuration Reference**: See `config.py`
- **API Documentation**: See docstrings in individual modules

---

**Version**: 2.0 (Refactored)  
**Last Updated**: March 2026

