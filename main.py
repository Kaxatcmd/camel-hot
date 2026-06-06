"""
DJ Harmonic Analyzer - Main Entry Point (GUI Version)
"""

import sys
import os
import traceback

# ---------------------------------------------------------------------------
# Startup diagnostic for frozen builds — shows exact import errors to user
# ---------------------------------------------------------------------------
if getattr(sys, 'frozen', False):
    _crash_log = os.path.join(
        os.environ.get('APPDATA', os.path.expanduser('~')),
        'CamelHot', 'startup_errors.log'
    )
    os.makedirs(os.path.dirname(_crash_log), exist_ok=True)

    def _check_import(module_name):
        try:
            __import__(module_name)
            return None
        except Exception as e:
            return f"[{module_name}] {type(e).__name__}: {e}\n{traceback.format_exc()}"

    _errors = []
    for _mod in ('numpy', 'scipy', 'soundfile', 'librosa'):
        _err = _check_import(_mod)
        if _err:
            _errors.append(_err)

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

import logging_config
from gui.main_window import main

# Initialize logging system
logging_config.setup_logging()

if __name__ == "__main__":
    main()
