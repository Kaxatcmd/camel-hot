"""
DJ Harmonic Analyzer — GUI Installer & Launcher

Cross-platform installer with PyQt5 interface.
Handles: Python version check, venv creation, dependency install, app launch.

Bootstrap note:
  The platform launchers (.bat / .command / run.sh) ensure PyQt5 is available
  before this script is called, so the GUI is always shown.
"""

import sys
import os
import subprocess
import shutil
import venv
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap guard: if PyQt5 is not yet available, install it silently first
# (this can happen if someone runs `python installer.py` directly)
# ---------------------------------------------------------------------------
try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QProgressBar, QTextEdit, QFrame, QSizePolicy,
        QMessageBox
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt5.QtGui import QFont, QColor, QPalette
    PYQT5_AVAILABLE = True
except ImportError:
    PYQT5_AVAILABLE = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
APP_NAME = "DJ Harmonic Analyzer"
REPO_DIR = Path(__file__).parent.resolve()
VENV_DIR = REPO_DIR / ".venv"
REQUIREMENTS = REPO_DIR / "requirements.txt"
PYTHON_MIN = (3, 8)

DARK_BG      = "#1a1a2e"
PANEL_BG     = "#16213e"
ACCENT       = "#e94560"
ACCENT_HOVER = "#c73652"
SUCCESS      = "#0f9b58"
TEXT_MAIN    = "#eaeaea"
TEXT_DIM     = "#888888"
LOG_BG       = "#0d0d1a"


# ---------------------------------------------------------------------------
# Worker thread — runs installation steps without blocking the UI
# ---------------------------------------------------------------------------
class InstallWorker(QThread):
    progress    = pyqtSignal(int)          # 0-100
    log_line    = pyqtSignal(str)          # log message
    step_label  = pyqtSignal(str)          # current step description
    finished    = pyqtSignal(bool, str)    # success, message

    def run(self):
        try:
            # Step 1 — Python version
            self.step_label.emit("Verificando versão do Python...")
            self.log_line.emit(f"Python {sys.version}")
            if sys.version_info < PYTHON_MIN:
                self.finished.emit(False,
                    f"Python {PYTHON_MIN[0]}.{PYTHON_MIN[1]}+ necessário.\n"
                    f"Versão atual: {sys.version_info.major}.{sys.version_info.minor}")
                return
            self.progress.emit(10)

            # Step 2 — Virtual environment
            self.step_label.emit("Preparando ambiente virtual...")
            python_exec = self._ensure_venv()
            self.progress.emit(35)

            # Step 3 — Dependencies
            self.step_label.emit("Instalando dependências...")
            self._install_deps(python_exec)
            self.progress.emit(90)

            # Step 4 — Done
            self.step_label.emit("Pronto!")
            self.progress.emit(100)
            self.finished.emit(True, python_exec)

        except Exception as exc:
            self.finished.emit(False, str(exc))

    # ------------------------------------------------------------------
    def _ensure_venv(self) -> str:
        """Create .venv if needed; return path to its python executable."""
        if VENV_DIR.exists():
            self.log_line.emit(f"Ambiente virtual encontrado: {VENV_DIR}")
        else:
            self.log_line.emit(f"Criando ambiente virtual em {VENV_DIR} ...")
            venv.create(str(VENV_DIR), with_pip=True)
            self.log_line.emit("Ambiente virtual criado.")

        # Resolve python executable inside venv
        if sys.platform == "win32":
            python_exec = str(VENV_DIR / "Scripts" / "python.exe")
        else:
            python_exec = str(VENV_DIR / "bin" / "python")

        if not Path(python_exec).exists():
            raise FileNotFoundError(f"Python não encontrado em: {python_exec}")

        return python_exec

    def _install_deps(self, python_exec: str):
        """Run pip install -r requirements.txt inside the venv."""
        cmd = [python_exec, "-m", "pip", "install", "--upgrade", "pip", "-q"]
        self._run_cmd(cmd)

        cmd = [python_exec, "-m", "pip", "install", "-r", str(REQUIREMENTS)]
        self._run_cmd(cmd)

    def _run_cmd(self, cmd: list):
        self.log_line.emit("$ " + " ".join(str(c) for c in cmd))
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(REPO_DIR)
        )
        for line in process.stdout:
            line = line.rstrip()
            if line:
                self.log_line.emit(line)
        process.wait()
        if process.returncode != 0:
            raise RuntimeError(f"Comando falhou com código {process.returncode}")


# ---------------------------------------------------------------------------
# Main installer window
# ---------------------------------------------------------------------------
class InstallerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.python_exec = None
        self._proc = None      # subprocess.Popen handle for the launched app
        self._build_ui()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        self.setWindowTitle(f"{APP_NAME} — Instalador")
        self.setMinimumSize(680, 520)
        self.setStyleSheet(f"background-color: {DARK_BG}; color: {TEXT_MAIN};")

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(18)

        # --- Title
        title = QLabel(APP_NAME)
        title.setFont(QFont("Arial", 22, QFont.Bold))
        title.setStyleSheet(f"color: {ACCENT};")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        subtitle = QLabel("Instalador & Lançador")
        subtitle.setFont(QFont("Arial", 11))
        subtitle.setStyleSheet(f"color: {TEXT_DIM};")
        subtitle.setAlignment(Qt.AlignCenter)
        root.addWidget(subtitle)

        # --- Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {PANEL_BG};")
        root.addWidget(sep)

        # --- Step label
        self.lbl_step = QLabel("Pronto para instalar.")
        self.lbl_step.setFont(QFont("Arial", 10))
        self.lbl_step.setStyleSheet(f"color: {TEXT_MAIN};")
        root.addWidget(self.lbl_step)

        # --- Progress bar
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(10)
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {PANEL_BG};
                border-radius: 5px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {ACCENT};
                border-radius: 5px;
            }}
        """)
        root.addWidget(self.progress)

        # --- Log output
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Courier New", 9))
        self.log.setStyleSheet(f"""
            QTextEdit {{
                background-color: {LOG_BG};
                color: #aaffaa;
                border: 1px solid {PANEL_BG};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        self.log.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(self.log)

        # --- Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.btn_install = QPushButton("⚙  Instalar")
        self.btn_install.setFixedHeight(44)
        self.btn_install.setFont(QFont("Arial", 11, QFont.Bold))
        self.btn_install.setCursor(Qt.PointingHandCursor)
        self.btn_install.setStyleSheet(self._btn_style(ACCENT, ACCENT_HOVER))
        self.btn_install.clicked.connect(self._start_install)
        btn_row.addWidget(self.btn_install)

        self.btn_launch = QPushButton("▶  Lançar Aplicação")
        self.btn_launch.setFixedHeight(44)
        self.btn_launch.setFont(QFont("Arial", 11, QFont.Bold))
        self.btn_launch.setCursor(Qt.PointingHandCursor)
        self.btn_launch.setStyleSheet(self._btn_style(SUCCESS, "#0a7a45"))
        self.btn_launch.clicked.connect(self._launch_app)
        self.btn_launch.setEnabled(False)
        btn_row.addWidget(self.btn_launch)

        root.addLayout(btn_row)

        # --- Footer
        footer = QLabel(f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}  |  {sys.platform}")
        footer.setFont(QFont("Arial", 8))
        footer.setStyleSheet(f"color: {TEXT_DIM};")
        footer.setAlignment(Qt.AlignCenter)
        root.addWidget(footer)

        # Auto-check if already installed
        QTimer.singleShot(200, self._check_already_installed)

    def _btn_style(self, bg: str, hover: str) -> str:
        return f"""
            QPushButton {{
                background-color: {bg};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 24px;
            }}
            QPushButton:hover {{ background-color: {hover}; }}
            QPushButton:disabled {{
                background-color: #333355;
                color: #666688;
            }}
        """

    # ---------------------------------------------------------------- Logic
    def _check_already_installed(self):
        """If .venv already has all deps, enable launch directly."""
        if sys.platform == "win32":
            python_exec = VENV_DIR / "Scripts" / "python.exe"
        else:
            python_exec = VENV_DIR / "bin" / "python"

        if python_exec.exists():
            result = subprocess.run(
                [str(python_exec), "-c",
                 "import librosa, PyQt5, matplotlib; print('ok')"],
                capture_output=True, text=True, cwd=str(REPO_DIR)
            )
            if result.stdout.strip() == "ok":
                self.python_exec = str(python_exec)
                self._log("✅ Dependências já instaladas.")
                self.lbl_step.setText("Tudo pronto — pode lançar a aplicação.")
                self.progress.setValue(100)
                self.btn_launch.setEnabled(True)
                return

        self._log("Clique em 'Instalar' para configurar o ambiente.")

    def _start_install(self):
        self.btn_install.setEnabled(False)
        self.btn_launch.setEnabled(False)
        self.log.clear()
        self.progress.setValue(0)

        self.worker = InstallWorker()
        self.worker.progress.connect(self.progress.setValue)
        self.worker.log_line.connect(self._log)
        self.worker.step_label.connect(self.lbl_step.setText)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

    def _on_finished(self, success: bool, message: str):
        if success:
            self.python_exec = message
            self._log("\n✅ Instalação concluída com sucesso!")
            self.lbl_step.setText("Instalação completa. Pode lançar a aplicação.")
            self.btn_launch.setEnabled(True)
        else:
            self._log(f"\n❌ Erro: {message}")
            self.lbl_step.setText("Instalação falhou. Veja o log acima.")
            self.btn_install.setEnabled(True)

    def _launch_app(self):
        if not self.python_exec:
            return

        # Preflight: verify critical imports are available in the venv
        self._log("\n🔍 Verificando dependências antes de lançar...")
        preflight = subprocess.run(
            [self.python_exec, "-c", "import librosa, soundfile, PyQt5"],
            capture_output=True, text=True, cwd=str(REPO_DIR)
        )
        if preflight.returncode != 0:
            err = (preflight.stderr.strip() or preflight.stdout.strip()
                   or "Erro desconhecido — sem saída capturada.")
            self._log(f"\n❌ Preflight falhou:\n{err}")
            QMessageBox.critical(
                self,
                "Verificação de dependências falhou",
                f"Não foi possível importar dependências críticas:\n\n{err}\n\n"
                "Por favor, reinstale a aplicação clicando em 'Instalar'."
            )
            return

        self._log("\n🚀 A lançar DJ Harmonic Analyzer...")
        self._proc = subprocess.Popen(
            [self.python_exec, str(REPO_DIR / "main.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(REPO_DIR)
        )
        # Check for an immediate crash after 3 seconds without blocking the UI
        QTimer.singleShot(3000, self._check_launch)

    def _check_launch(self):
        """Called 3 s after launching — if the process already exited it crashed."""
        if self._proc is None:
            return
        exit_code = self._proc.poll()
        if exit_code is not None:
            # Process exited early — read all output and surface it
            stdout = self._proc.stdout.read()
            stderr = self._proc.stderr.read()
            output = stderr.strip() or stdout.strip() or "Sem saída capturada."
            self._log(f"\n❌ Aplicação encerrou inesperadamente (código {exit_code}):\n{output}")
            QMessageBox.critical(
                self,
                "Aplicação encerrou inesperadamente",
                f"DJ Harmonic Analyzer encerrou imediatamente após o lançamento "
                f"(código de saída: {exit_code}).\n\n{output}"
            )
        else:
            # Still running — launched successfully
            self._log("✅ Aplicação iniciada com sucesso.")
            self.close()

    def _log(self, text: str):
        self.log.append(text)
        self.log.verticalScrollBar().setValue(
            self.log.verticalScrollBar().maximum()
        )


# ---------------------------------------------------------------------------
# Bootstrap: ensure PyQt5 is available before opening the window
# ---------------------------------------------------------------------------
def _bootstrap_pyqt5():
    """Install PyQt5 into the system/user Python if not yet available."""
    print("[installer] PyQt5 não encontrado — instalando bootstrap mínimo...")
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                           "PyQt5>=5.15.0", "--quiet"])
    print("[installer] PyQt5 instalado. Relançando...")
    os.execv(sys.executable, [sys.executable] + sys.argv)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    if not PYQT5_AVAILABLE:
        _bootstrap_pyqt5()
        return  # execv replaces process; this line is never reached

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")

    # Apply dark palette globally
    palette = QPalette()
    palette.setColor(QPalette.Window,          QColor(DARK_BG))
    palette.setColor(QPalette.WindowText,      QColor(TEXT_MAIN))
    palette.setColor(QPalette.Base,            QColor(LOG_BG))
    palette.setColor(QPalette.AlternateBase,   QColor(PANEL_BG))
    palette.setColor(QPalette.Button,          QColor(PANEL_BG))
    palette.setColor(QPalette.ButtonText,      QColor(TEXT_MAIN))
    palette.setColor(QPalette.Highlight,       QColor(ACCENT))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    win = InstallerWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
