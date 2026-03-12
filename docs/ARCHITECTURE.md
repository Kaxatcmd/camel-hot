## Architecture Overview

DJ Harmonic Analyzer is designed with a layered architecture separating concerns and enabling cross-platform compatibility.

### Architecture Layers

```
┌─────────────────────────────────────┐
│      Application Entry (main.py)    │
│   - Logging initialization          │
│   - GUI launching                   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│    GUI Layer (gui/main_window.py)   │
│   - PyQt5 interface                 │
│   - User interactions               │
│   - Threading for non-blocking ops  │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Business Logic Layer           │
│  ┌──────────────────────────────┐   │
│  │  File Organization (organizer.py)│
│  │  - File discovery            │   │
│  │  - Batch operations          │   │
│  │  - Playlist generation       │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │  Analysis (audio_analysis/)  │   │
│  │  - Key detection             │   │
│  │  - BPM detection             │   │
│  │  - Groove analysis           │   │
│  │  - Mood classification       │   │
│  │  - Energy detection          │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │  Utilities (utils/)          │   │
│  │  - Camelot mapping           │   │
│  │  - Transition scoring        │   │
│  │  - Translations              │   │
│  └──────────────────────────────┘   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│    Infrastructure Layer             │
│  - config.py: Configuration         │
│  - logging_config.py: Logging      │
│  - pathlib: Cross-platform paths    │
└─────────────────────────────────────┘
```

### Design Patterns

#### 1. **Configuration as Code**
- Centralized configuration in `config.py`
- All hardcoded values extracted and parameterized
- Environment-aware (frozen vs. normal execution)

#### 2. **Structured Logging**
- Application-wide logging infrastructure (`logging_config.py`)
- Replaces print statements with proper logging
- File rotation and level control

#### 3. **Cross-Platform Abstractions**
- `pathlib.Path` for all file operations
- No hardcoded separators or OS-specific code
- Frozen environment support for packaging tools

#### 4. **Separation of Concerns**
- **GUI**: User interface only (PyQt5)
- **Analysis**: Algorithmic work (librosa, numpy)
- **Organization**: File operations (pathlib)
- **Utilities**: Helper functions (Camelot, transitions, translations)
- **Infrastructure**: Configuration and logging

#### 5. **Threading for Responsiveness**
- `AnalysisWorker` thread in `gui/main_window.py`
- Long-running analysis doesn't block UI
- Signal-based communication between threads

### Data Flow

#### Single Track Analysis
```
File Path
   │
   ▼
analyze_track()
   │
   ├─→ detect_key_from_audio() ──→ Camelot Key
   ├─→ detect_bpm() ──────────────→ BPM
   ├─→ analyze_groove() ──────────→ Groove Type
   ├─→ classify_mood() ───────────→ Mood
   └─→ analyze_energy() ──────────→ Energy
   │
   ▼
Analysis Result Dictionary
   │
   ▼
GUI Update / File Organization
```

#### Batch Organization
```
Directory Path
   │
   ▼
find_audio_files()
   │
   ▼
For each file:
   ├─→ analyze_track()
   ├─→ Extract Camelot key
   └─→ Copy/Move to key folder
   │
   ▼
Organized Structure:
   8A/
   8B/
   9A/
   ...
```

#### Playlist Generation
```
Directory → find_audio_files()
              │
              ├─→ Analyze all files
              ├─→ Filter (key, BPM, compatibility)
              └─→ Sort (harmonic path)
              │
              ▼
         Generate M3U File
```

### Module Dependencies

```
main.py
   ├─→ config.py (paths, settings)
   ├─→ logging_config.py (logging setup)
   └─→ gui/main_window.py
       ├─→ config.py (assets dir)
       ├─→ audio_analysis/key_detection.py
       ├─→ gui/file_manager/organizer.py
       ├─→ utils/camelot_map.py
       ├─→ utils/transition_scoring.py
       ├─→ utils/translations.py
       └─→ utils/dj_tips.py

gui/file_manager/organizer.py
   ├─→ audio_analysis/key_detection.py
   ├─→ utils/camelot_map.py
   └─→ utils/camelot_wheel_generator.py

audio_analysis/*
   ├─→ logging_config (error logging)
   ├─→ librosa (audio processing)
   └─→ numpy (signal processing)
```

### Key Interfaces

#### `analyze_track(file_path)` → dict
```python
{
    'file_path': str,
    'key': str,  # Musical note (e.g., "C major")
    'camelot': str,  # Camelot notation (e.g., "8A")
    'bpm': int,
    'duration': float,  # seconds
    'confidence': float,  # 0.0-1.0
    # Additional analysis...
}
```

#### `organize_by_key(input_dir, output_dir, move_files=False)` → dict
```python
{
    'total_files': int,
    'organized_count': int,
    'errors': list,
    'by_key': {
        '8A': [files],
        '9B': [files],
        ...
    }
}
```

#### `create_playlist(input_dir, output_file, **options)` → list
Returns list of file paths in generated M3U playlist.

### Configuration Constants

All configuration is centralized in `config.py`:
- **Paths**: `BASE_DIR`, `ASSETS_DIR`, `LOGS_DIR`, `DATA_DIR`
- **Audio**: `AUDIO_LOAD_DURATION_SHORT`, `AUDIO_LOAD_DURATION_LONG`, `PEAK_PICK_PARAMS`
- **GUI**: `THEME_GRADIENT_COLORS`, `AUDIO_FILE_FILTER`
- **Logging**: `LOG_LEVEL`, `LOG_FORMAT`, `LOG_MAX_BYTES`
- **Behavior**: `DEFAULT_MOVE_FILES`, `DEFAULT_PLAYLIST_LIMIT`

### Error Handling

1. **Audio Analysis Errors**:
   - Logged via `logger.error()` (structured logging)
   - Returns fallback values or None
   - GUI displays error message to user

2. **File Operation Errors**:
   - Caught and reported in operation result dictionary
   - User can retry or skip problematic files

3. **UI Errors**:
   - Displayed via `QMessageBox`
   - Logged for debugging

### Thread Safety

- **UI Thread**: Handles all PyQt5 operations
- **Worker Thread** (`AnalysisWorker`): Handles analysis operations
- **Communication**: Signals (pyqtSignal) for thread-safe messaging
- **No Shared Mutable State**: Each thread has its own data

### Performance Considerations

1. **Audio Loading**:
   - Limited to 30-60 seconds per file (configurable)
   - Reduces memory usage and analysis time
   - Sufficient for key and BPM detection

2. **Batch Operations**:
   - Sequential processing (no parallelization)
   - Simpler error handling and UI updates
   - Extensible to multi-threading if needed

3. **Caching Opportunities**:
   - Analysis results could be cached
   - File metadata could be stored in SQLite
   - Future enhancement: avoid re-analyzing unchanged files

### Extensibility Points

1. **New Analysis Features**:
   - Add modules to `audio_analysis/`
   - Integrate results into `analyze_track()`

2. **New Playlist Strategies**:
   - Add functions to `gui/file_manager/organizer.py`
   - Expose via GUI buttons

3. **Additional Languages**:
   - Add translation dictionary to `utils/translations.py`

4. **Custom Themes**:
   - Define color schemes in `config.py`
   - Update GUI stylesheet in `main_window.py`

### Testing Strategy

- **Unit Tests**: `test_setup.py` (Camelot mapping, file operations)
- **Integration Tests**: `test_gui.py` (GUI import and startup)
- **Demo/Showcase**: `test_transition_engine.py` (full workflows)
- **Manual Testing**: Visual verification of organization and playlists

---

**Architecture Version**: 2.0 (Refactored, 2026)
