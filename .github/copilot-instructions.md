# Copilot / AI Agent Instructions for DJ Harmonic Analyzer

Purpose: give an AI coding agent immediate, actionable context to be productive in this repo.

- **Big picture:** This is a PyQt5 GUI app (entry: `main.py`) that analyzes audio files (librosa) to detect key/BPM, maps keys to Camelot notation, and organizes music into folders/playlists. Core steps: audio load → pitch/chroma analysis → map to Camelot (`utils/camelot_map.py`) → file ops (`file_manager/organizaer.py`) or GUI actions (`gui/main_window.py`).

- **Key files to read first:**
  - `main.py` — app entry point (launches GUI)
  - `gui/main_window.py` — PyQt5 GUI, worker thread pattern (`AnalysisWorker`) and UI wiring
  - `audio_analysis/key_detection.py` — core analysis functions, central: `analyze_track()` and `detect_key_from_audio()`
  - `file_manager/organizaer.py` — `find_audio_files()`, `organize_by_key()`, `create_playlist()` (M3U generation)
  - `utils/camelot_map.py` — canonical Camelot mapping (`CAMELOT_MAP`) and compatibility helpers (`is_compatible_keys()`)

- **Run / dev tasks (exact commands):**
  - Activate venv: `source venv/bin/activate`
  - Install deps: `pip install -r requirements.txt`
  - Quick checks: `python test_setup.py` and `python test_gui.py`
  - Run app: `python main.py` (opens the GUI)
  - Convenience script: `./run.sh` runs tests then starts the app

- **Project-specific patterns & conventions:**
  - GUI-first design: CLI code remains for reference but main UX is PyQt5 GUI (`DJAnalyzerGUI`). Prefer updating GUI wiring when adding features.
  - Analysis functions are synchronous but used from a QThread (`AnalysisWorker`) to avoid blocking UI — follow that pattern when adding heavy work.
  - Audio analysis may run without `librosa` installed (module checks). Tests guard around this; always check for `LIBROSA_AVAILABLE` in `audio_analysis/key_detection.py`.
  - Camelot codes are used across the codebase (strings like `8A`, `8B`); use `utils.camelot_map` helpers to convert/compare.
  - File operations: `organize_by_key()` defaults to copying; `move_files` flag controls destructive behavior. Avoid changing default to move without prompting.

- **When editing analysis code:**
  - Add unit checks in `test_setup.py` for any new `utils.camelot_map` behavior.
  - For `analyze_track()` changes, run `test_setup.py` with at least one audio sample in `input_audio/` or mock the call in tests.
  - Maintain the `analyze_track()` return shape: `{file_path, key, camelot, bpm, duration, confidence}` — GUI and file manager expect these keys.

- **Debugging tips:**
  - If GUI fails to import, run `python -c "from gui.main_window import DJAnalyzerGUI"` to reproduce import errors.
  - If audio analysis returns 'Unknown', check `librosa` installation and try analyzing a known-good file from `input_audio/`.
  - Use `run.sh` to validate the environment quickly; it activates venv, installs deps, runs tests, then launches GUI.

- **PR guidance for agents:**
  - Keep changes minimal and focused; update `test_setup.py` if behavior or surface area changes.
  - Reference the GUI wiring in `gui/main_window.py` when adding new features that touch UI elements.
  - Do not change Camelot mapping keys without updating `utils/camelot_map.py` and tests.

If anything above is unclear or you want me to expand a section (e.g., add quick code examples for modifying `analyze_track()` or a sample unit test), tell me which part to expand.
