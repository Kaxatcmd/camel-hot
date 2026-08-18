"""
DJ Harmonic Analyzer - Main Entry Point (GUI Version)
"""

import sys
import os
import math
import tempfile
import wave

import logging_config


# Configure the rotating file logger before any frozen-runtime diagnostics.
logging_config.setup_logging()


def _run_smoke_test():
    """Exercise the packaged analysis stack without opening the GUI."""
    from audio_analysis.runtime_check import check_analysis_runtime

    errors = check_analysis_runtime()
    if errors:
        print("Audio runtime check failed:\n" + "\n".join(errors), file=sys.stderr)
        return 1

    from audio_analysis.key_detection import analyze_track

    sample_rate = 22050
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as audio_file:
        sample_path = audio_file.name
    try:
        with wave.open(sample_path, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            samples = (
                int(0.25 * 32767 * math.sin(2 * math.pi * 440 * index / sample_rate))
                for index in range(sample_rate * 4)
            )
            wav_file.writeframes(b"".join(sample.to_bytes(2, "little", signed=True) for sample in samples))
        result = analyze_track(sample_path)
        if result.get("camelot") == "Unknown" or result.get("error"):
            print(f"Audio analysis smoke test failed: {result}", file=sys.stderr)
            return 1
        print("Packaged audio runtime smoke test: OK")
        return 0
    finally:
        try:
            os.remove(sample_path)
        except OSError:
            pass


if "--smoke-test" in sys.argv:
    sys.exit(_run_smoke_test())

# ---------------------------------------------------------------------------
# Startup diagnostic for frozen builds — shows exact import errors to user
# ---------------------------------------------------------------------------
if getattr(sys, 'frozen', False):
    _crash_log = os.path.join(
        os.environ.get('APPDATA', os.path.expanduser('~')),
        'CamelHot', 'startup_errors.log'
    )
    os.makedirs(os.path.dirname(_crash_log), exist_ok=True)

    from audio_analysis.runtime_check import check_analysis_runtime

    _errors = check_analysis_runtime()

    if _errors:
        _msg = "CAMEL-HOT startup error — audio analysis will not work.\n\n"
        _msg += "\n\n".join(_errors)
        # Write to log file
        try:
            with open(_crash_log, 'w') as _f:
                _f.write(_msg)
        except OSError:
            pass
        # Show dialog
        from PyQt5.QtWidgets import QApplication, QMessageBox
        _app = QApplication.instance() or QApplication(sys.argv)
        _dlg = QMessageBox()
        _dlg.setIcon(QMessageBox.Critical)
        _dlg.setWindowTitle("CamelHot — Erro de Arranque")
        _dlg.setText("Erro ao carregar módulos de análise de áudio:")
        _dlg.setDetailedText(_msg)
        _dlg.setInformativeText(f"Detalhes guardados em:\n{_crash_log}")
        _dlg.exec_()

from gui.main_window import main

if __name__ == "__main__":
    main()
