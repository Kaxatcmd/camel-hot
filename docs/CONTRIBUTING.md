# Contributing to Camel-Hot

Thank you for your interest in contributing! This guide covers everything you need to get started.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Architecture Notes](#architecture-notes)

---

## Code of Conduct

Be respectful and constructive. Contributions of all skill levels are welcome.

---

## Getting Started

### Prerequisites

- Python 3.8+
- `git`
- A Linux/macOS/Windows machine (all three are CI-tested)

### 1. Fork and clone

```bash
git clone https://github.com/your-username/camel-hot.git
cd camel-hot
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 3. Install in development mode

```bash
pip install -r requirements.txt
pip install pytest pytest-cov flake8
```

### 4. Verify the setup

```bash
python test_setup.py             # Quick sanity check
python -m pytest tests/unit/ -v  # Run the unit test suite
```

---

## Project Structure

```
camel-hot/
├── main.py                  # Entry point — calls gui/main_window.main()
├── config.py                # All tuneable constants and path helpers
├── logging_config.py        # Structured log setup (file + console)
│
├── audio_analysis/          # Business logic — NO PyQt5 imports here
│   ├── key_detection.py     # analyze_track() orchestrator
│   ├── energy_detection.py
│   ├── groove_analysis.py
│   └── mood_classification.py
│
├── gui/
│   ├── main_window.py       # PyQt5 window, workers (QThread), dialogs
│   └── file_manager/
│       └── organizer.py     # File discovery, copy/organize, M3U generation
│
├── utils/
│   ├── camelot_map.py       # CAMELOT_MAP + compatibility helpers
│   ├── transition_scoring.py
│   ├── translations.py
│   └── dj_tips.py
│
├── tests/
│   ├── conftest.py          # Shared fixtures (tmp dirs, audio file helpers)
│   └── unit/                # Fast tests — no audio files, no display required
│       ├── test_camelot_map.py
│       ├── test_organizer.py
│       ├── test_transition_scoring.py
│       └── test_config.py
│
├── docs/                    # Architecture, configuration, Camelot reference
├── assets/                  # Images used by the GUI
└── .github/
    ├── workflows/ci.yml     # GitHub Actions (pytest + flake8)
    └── ISSUE_TEMPLATE/
```

---

## Development Workflow

### Branching model

| Branch | Purpose |
|--------|---------|
| `main` | Stable releases only |
| `develop` | Integration branch — PRs target here |
| `feature/<name>` | New features |
| `fix/<name>` | Bug fixes |
| `docs/<name>` | Documentation changes |

```bash
git checkout develop
git checkout -b feature/my-new-feature
```

### Commit messages

Use the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <short summary>

[optional body]
[optional footer]
```

| Type | When to use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `test` | Adding or updating tests |
| `docs` | Documentation only |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `chore` | Build process, dependency updates |

Examples:
```
feat(playlist): add energy-aware track sequencing
fix(organizer): handle filenames with Unicode characters
test(camelot_map): add wraparound compatibility tests
```

---

## Code Standards

### Style

- PEP 8. Line length: **100 characters** max.
- Use `pathlib.Path` for all file system operations — no `os.path.join`.
- No bare `except:` clauses — always catch specific exceptions.
- All public functions must have a one-line docstring minimum.

### Separation of concerns (critical)

| Layer | Rule |
|-------|------|
| `audio_analysis/` | **Zero** PyQt5 imports. Pure Python + librosa/numpy only. |
| `utils/` | **Zero** PyQt5 imports. Pure Python + stdlib. |
| `gui/` | May import from `audio_analysis/` and `utils/`. Never the reverse. |
| `config.py` | No imports from `audio_analysis/`, `gui/`, or `utils/`. |

### Worker / threading pattern

Long-running operations **must** run in a `QThread` subclass, never on the main thread.
Follow the existing pattern in `gui/main_window.py`:

```python
class MyWorker(QThread):
    finished  = pyqtSignal()
    result    = pyqtSignal(dict)
    error     = pyqtSignal(str)
    progress  = pyqtSignal(int, str)    # 0-100, message
    file_tick = pyqtSignal(str, int, int)  # filename, idx, total

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            # ... do work, check self._cancelled periodically ...
            self.result.emit(data)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit()
```

### analyze_track() return contract

`analyze_track()` must always return a dict with **at least** these keys.
GUI code and `organizer.py` both depend on this shape:

```python
{
    "file_path": str,
    "key":       str,     # e.g. "C Major" — "Unknown" on failure
    "camelot":   str,     # e.g. "8B"      — "Unknown" on failure
    "bpm":       int,
    "duration":  float,   # seconds
    "confidence": float,  # 0.0 – 1.0
}
```

### Camelot codes

Always use `utils/camelot_map.py` functions — never construct Camelot strings manually.

---

## Testing

### Run all unit tests

```bash
python -m pytest tests/unit/ -v
```

### Run with coverage

```bash
python -m pytest tests/unit/ --cov=audio_analysis --cov=gui/file_manager \
    --cov=utils --cov=config --cov-report=term-missing
```

### Test markers

| Marker | Meaning |
|--------|---------|
| `unit` | Fast — no audio files, no display |
| `integration` | Needs real MP3s in `input_audio/` |
| `gui` | Needs a Qt display (Xvfb on Linux) |

```bash
# Skip integration and gui tests
python -m pytest tests/ -m "not integration and not gui"
```

### Adding new tests

- New business logic → add a test in `tests/unit/`.
- Keep unit tests free of real file I/O — use `tmp_path` and `unittest.mock.patch`.
- New `analyze_track()` behaviour → update the test in `test_organizer.py` that mocks `analyze_track`.
- Use the fixtures from `tests/conftest.py` (`tmp_input`, `tmp_output`, etc.).

---

## Submitting Changes

1. Make sure all unit tests pass: `python -m pytest tests/unit/ -v`
2. Make sure flake8 reports no errors: `flake8 . --select=E9,F63,F7,F82 --exclude=venv,.venv`
3. Push your branch and open a Pull Request **targeting `develop`**.
4. Fill in the PR template (what changed, why, how to test).
5. A CI run will be triggered automatically — fix any failures before requesting review.

---

## Architecture Notes

### librosa availability guard

`librosa` is an optional runtime dependency. Always guard imports:

```python
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
```

Functions that need it should return a safe fallback (not raise) when it's absent.

### Progress callbacks

Operations in `organizer.py` accept a `progress_callback(filename, idx, total) -> bool`.
Return `True` from the callback to cancel the loop. The caller (GUI worker) connects
the `RealTimeProgressDialog.cancelled` signal to `worker.cancel()`.

### Theme system

`DJAnalyzerGUI._dark: bool` tracks the current theme.
All dialogs accept `dark=bool` in their constructors and call `_apply_theme()` in `__init__`.
Do not hardcode colour literals anywhere in the GUI — use the theme palette.
