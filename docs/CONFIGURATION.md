## Configuration Reference

All configurable parameters for DJ Harmonic Analyzer are centralized in `config.py`. This document explains each configuration option.

### File Structure

```
config.py
├── BASE PATHS
├── AUDIO ANALYSIS PARAMETERS
├── PLAYLIST & FILE ORGANIZATION
├── GUI THEME & COLORS
├── LOGGING CONFIGURATION
└── HELPER FUNCTIONS
```

### Base Paths

These paths define where the application stores files and data.

#### `BASE_DIR` (Path)
The root directory of the application. Automatically determined at runtime:
- **Normal execution**: Parent directory of `config.py`
- **Frozen execution** (PyInstaller): `sys._MEIPASS`

#### `PROJECT_ROOT` (Path)
Alias for `BASE_DIR`. Use this to reference project-relative paths.

#### `ASSETS_DIR` (Path)
Location of images, icons, and logos: `PROJECT_ROOT / "assets"`

#### `INPUT_AUDIO_DIR` (Path)
Default directory for batch audio processing: `PROJECT_ROOT / "input_audio"`

#### `OUTPUT_AUDIO_DIR` (Path)
Default directory for organized output: `PROJECT_ROOT / "output_audio"`

#### `LOGS_DIR` (Path)
Directory where `dj_analyzer.log` is stored: `PROJECT_ROOT / "logs"`

#### `DOCS_DIR` (Path)
Documentation directory: `PROJECT_ROOT / "docs"`

#### `DATA_DIR` (Path)
Runtime data files: `PROJECT_ROOT / "data"`

### Audio Analysis Parameters

These parameters control how audio is analyzed.

#### `AUDIO_LOAD_DURATION_SHORT` (int)
Duration in seconds for key detection analysis: **30 seconds**

- Faster key detection
- Sufficient for most reliable key extraction
- Reduces memory usage

#### `AUDIO_LOAD_DURATION_LONG` (int)
Duration in seconds for full track analysis: **60 seconds**

- Includes BPM and advanced features
- Higher accuracy for complex arrangements
- Longer processing time

#### `PEAK_PICK_PARAMS` (dict)
Parameters for librosa's onset detection peak picking:

```python
{
    "pre_max": 3,        # Pre peak samples
    "post_max": 3,       # Post peak samples
    "pre_avg": 3,        # Pre average window
    "post_avg": 3,       # Post average window
    "delta": 0.0,        # Energy threshold
    "wait": 10,          # Minimum sample spacing
}
```

**Advanced**: These are passed directly to `librosa.util.peak_pick()`. Adjust if onset detection feels too sensitive or insensitive.

#### `KICK_REGULARITY_FALLBACK` (float)
Value (0.0-1.0) returned when kick detection fails: **0.3**

#### `KICK_REGULARITY_NO_LIBROSA` (float)
Value (0.0-1.0) used when librosa is unavailable: **0.5**

#### `PERCUSSION_DENSITY_FALLBACK` (float)
Value (0.0-1.0) returned when percussion detection fails: **0.3**

#### `SWING_THRESHOLDS` (dict)
Swing classification boundaries:

```python
{
    "none": 0.1,          # < 0.1: No swing (quantized)
    "light": 0.5,         # 0.1-0.5: Light swing
    "moderate": 0.8,      # 0.5-0.8: Moderate swing
    "strong": 0.9,        # 0.8+: Strong swing
}
```

#### `DISSONANT_INTERVALS` (list)
Semitone intervals considered dissonant: **[1, 6, 11]**

- Used in mood/tension detection
- Semitones from root note

#### `ATTACK_STEEPNESS_FALLBACK` (float)
Value (0.0-1.0) used when attack detection fails: **0.3**

### Playlist & File Organization

#### `DEFAULT_PLAYLIST_LIMIT` (int)
Maximum songs in a generated playlist: **20**

- Prevents excessive file lists
- Adjustable per playlist via GUI

#### `SUPPORTED_AUDIO_EXTENSIONS` (list)
Recognized audio file extensions:

```python
[".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aiff"]
```

**Adding formats**: Add extension (lowercase with dot) to this list. Ensure your OS and librosa support the codec.

#### `DEFAULT_MOVE_FILES` (bool)
Default file operation behavior: **False** (copy instead of move)

- `False`: Copies files to output (safer, keeps originals)
- `True`: Moves files (destructive, removes originals)

### GUI Theme & Colors

#### `THEME_GRADIENT_COLORS` (dict)
Desert Sunset theme colors used throughout the GUI:

```python
{
    "dark_green": "#1a4d2e",
    "medium_green": "#3d6e40",
    "light_yellow": "#f4d03f",
    "orange": "#ff9500",
    "dark_orange": "#f07c1e",
    "burgundy": "#c1440e",
}
```

**Customizing**: Modify hex color codes to create custom themes.

#### `AUDIO_FILE_FILTER` (str)
File dialog filter text for audio files:

```
"Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a *.aiff);;All Files (*)"
```

### Logging Configuration

#### `LOG_LEVEL` (str)
Default logging level: **"INFO"**

Options: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`

- `DEBUG`: Detailed analysis steps
- `INFO`: General operation information
- `WARNING`: Potential issues (non-fatal)
- `ERROR`: Errors that prevent operation
- `CRITICAL`: Severe errors requiring exit

#### `LOG_FORMAT` (str)
Format string for log messages:

```
"%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

#### `LOG_FILE` (str)
Log filename: **"dj_analyzer.log"**

Stored in `LOGS_DIR`. Use `%(asctime)s` in filename for dated logs.

#### `LOG_MAX_BYTES` (int)
Maximum size before log rotation: **5,242,880 bytes (5 MB)**

- Prevents disk space issues
- Automatic file rotation occurs at limit

#### `LOG_BACKUP_COUNT` (int)
Number of backup log files to keep: **3**

- Older logs are deleted automatically
- Configure for compliance/audit requirements

### Helper Functions

#### `get_assets_dir()` → Path
Returns `ASSETS_DIR`, creating it if necessary.

```python
from config import get_assets_dir
assets = get_assets_dir()  # Path object
logo_path = assets / "camel_mascot.png"
```

#### `get_logs_dir()` → Path
Returns `LOGS_DIR`, creating it if necessary.

```python
from config import get_logs_dir
logs = get_logs_dir()
```

#### `get_data_dir()` → Path
Returns `DATA_DIR`, creating it if necessary.

```python
from config import get_data_dir
data = get_data_dir()
```

#### `get_input_audio_dir()` → Path
Returns `INPUT_AUDIO_DIR`, creating it if necessary.

```python
from config import get_input_audio_dir
input_dir = get_input_audio_dir()
```

#### `get_output_audio_dir()` → Path
Returns `OUTPUT_AUDIO_DIR`, creating it if necessary.

```python
from config import get_output_audio_dir
output_dir = get_output_audio_dir()
```

#### `ensure_dirs()` → None
Creates all required directories at once.

```python
from config import ensure_dirs
ensure_dirs()  # Safe to call multiple times
```

### Usage Examples

#### Customizing Audio Analysis Duration

```python
# In config.py
AUDIO_LOAD_DURATION_LONG = 120  # Analyze 2 minutes instead of 1
```

#### Enabling Debug Logging

```python
# In config.py
LOG_LEVEL = "DEBUG"
```

#### Adding a New Audio Format

```python
# In config.py
SUPPORTED_AUDIO_EXTENSIONS = [
    ".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aiff",
    ".opus",  # Add new format
]
```

#### Customizing Theme Colors

```python
# In config.py - Use a cool blue theme
THEME_GRADIENT_COLORS = {
    "dark_green": "#1a3a52",      # Dark blue
    "medium_green": "#2d5a8c",    # Medium blue
    "light_yellow": "#a8dadc",    # Light blue
    "orange": "#4ca3dd",          # Sky blue
    "dark_orange": "#2d7dbf",     # Deep blue
    "burgundy": "#1d4f7c",        # Navy
}
```

#### Changing Default Directory Behavior

```python
# In config.py - Move files by default (destructive!)
DEFAULT_MOVE_FILES = True
```

### Best Practices

1. **Keep Backups**: Before changing configuration, save the original `config.py`

2. **Test Changes**: After configuration changes, test with a small set of files

3. **Use Absolute Numbers**: Don't use relative multipliers or formulas in config - be explicit

4. **Document Custom Values**: Add comments for non-standard configurations

5. **Cross-Platform Paths**: Always use `Path` or `/` separators, never `\`

6. **Avoid Absolute Paths**: All paths should be relative to `BASE_DIR`

### Environment Variables

Future enhancement: Configuration can be leveraged via environment variables:

```bash
export DJ_LOG_LEVEL=DEBUG
export DJ_AUDIO_DURATION=120
python main.py
```

This would require updating `config.py` to check `os.environ`.

### Troubleshooting Configuration

#### "Permission denied" when writing logs
- Check `LOGS_DIR` permissions
- Ensure user has write access
- Verify disk space available

#### Audio files not found
- Check `INPUT_AUDIO_DIR` path
- Verify audio file extensions in `SUPPORTED_AUDIO_EXTENSIONS`
- Ensure files are in correct format

#### Files not organized correctly
- Verify `OUTPUT_AUDIO_DIR` exists and is writable
- Check `DEFAULT_MOVE_FILES` setting
- Review `SUPPORTED_AUDIO_EXTENSIONS`

#### Slow analysis
- Reduce `AUDIO_LOAD_DURATION_LONG` (faster but less accurate)
- Check system resources
- Verify audio format is supported

---

**Configuration Reference Version**: 2.0 (2026)
