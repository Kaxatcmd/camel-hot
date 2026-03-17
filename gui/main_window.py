"""
Main Window - Janela Principal da Aplicação (PyQt5)

Esta é a interface gráfica principal do DJ Harmonic Analyzer.
Implementada com PyQt5 para melhor compatibilidade e aparência profissional.
"""

import sys
import os
import re
import time
import subprocess
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QLineEdit, QFileDialog, QTextEdit,
    QComboBox, QSpinBox, QCheckBox, QMessageBox, QProgressDialog, QFrame,
    QRadioButton, QButtonGroup, QScrollArea, QSizePolicy, QStackedWidget,
    QDialog, QProgressBar, QGridLayout, QDesktopWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QRectF, QSettings, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QIcon, QColor, QLinearGradient, QPalette, QPixmap, QPainter, QPainterPath
from PyQt5.QtSvg import QSvgWidget, QSvgRenderer

from config import get_assets_dir
from audio_analysis.key_detection import analyze_track
from gui.file_manager.organizer import (
    find_audio_files, organize_by_key, create_harmonic_playlist,
    create_harmonic_sequence_playlist, create_key_to_key_playlist,
    create_camelot_zone_playlist, get_next_org_number
)
from utils.camelot_map import CAMELOT_MAP, get_compatible_keys
from utils.transition_scoring import calculate_transition_score
from utils.translations import Translator
from utils.dj_tips import DJTipsManager


_SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


class RealTimeProgressDialog(QDialog):
    """
    Reusable real-time progress dialog for file-processing operations.

    Features:
    - Animated spinner indicator
    - Smooth QPropertyAnimation progress bar
    - Per-file status (filename + X of Y)
    - Live stats: processed, remaining, speed, ETA, elapsed
    - Cancel and Close buttons
    - Full day/night theme support
    """

    cancelled = pyqtSignal()

    def __init__(self, parent=None, title="Processing...", dark=False, total_files=0):
        super().__init__(parent)
        self._dark = dark
        self._start_time = None
        self._files_processed = 0
        self._total_files = total_files
        self._spinner_idx = 0
        self._is_processing = True

        self.setWindowTitle(title)
        # Scale dialog size relative to available screen space
        screen = QDesktopWidget().availableGeometry(self)
        dlg_w = max(520, min(680, int(screen.width() * 0.40)))
        dlg_h = max(340, min(440, int(screen.height() * 0.46)))
        self.setMinimumSize(480, 320)
        self.resize(dlg_w, dlg_h)
        self.setModal(True)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

        self._build_ui()
        self._apply_theme()
        self._setup_timers()

        if parent:
            pr = parent.geometry()
            self.move(
                pr.center().x() - self.width() // 2,
                pr.center().y() - self.height() // 2,
            )

    # ── UI construction ────────────────────────────────────────────────────
    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(10)

        # Header row: title + spinner
        header_row = QHBoxLayout()
        self.title_lbl = QLabel("Processing...")
        self.title_lbl.setFont(QFont("Inter", 13, QFont.Bold))
        self.title_lbl.setObjectName("rtpd_title")
        header_row.addWidget(self.title_lbl)
        header_row.addStretch()
        self.spinner_lbl = QLabel(_SPINNER_FRAMES[0])
        self.spinner_lbl.setObjectName("rtpd_spinner")
        self.spinner_lbl.setFont(QFont("Courier New", 17))
        self.spinner_lbl.setAlignment(Qt.AlignCenter)
        self.spinner_lbl.setMinimumWidth(28)
        header_row.addWidget(self.spinner_lbl)
        layout.addLayout(header_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("rtpd_sep")
        layout.addWidget(sep)

        # Progress bar + percentage
        pb_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimumHeight(22)
        self.progress_bar.setObjectName("rtpd_bar")
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        pb_row.addWidget(self.progress_bar)
        self.pct_lbl = QLabel("0%")
        self.pct_lbl.setObjectName("rtpd_pct")
        self.pct_lbl.setMinimumWidth(42)
        self.pct_lbl.setAlignment(Qt.AlignCenter)
        self.pct_lbl.setFont(QFont("Inter", 10, QFont.Bold))
        pb_row.addWidget(self.pct_lbl)
        layout.addLayout(pb_row)

        # Status message
        self.status_lbl = QLabel("Initializing…")
        self.status_lbl.setObjectName("rtpd_status")
        self.status_lbl.setWordWrap(True)
        layout.addWidget(self.status_lbl)

        # Current file label
        self.file_lbl = QLabel("")
        self.file_lbl.setObjectName("rtpd_file")
        self.file_lbl.setWordWrap(True)
        layout.addWidget(self.file_lbl)

        # Stats grid
        stats_frame = QFrame()
        stats_frame.setObjectName("rtpd_stats_frame")
        sg = QGridLayout()
        sg.setContentsMargins(14, 8, 14, 8)
        sg.setVerticalSpacing(5)
        sg.setHorizontalSpacing(20)

        def _pair(label, obj):
            k = QLabel(label + ":")
            k.setObjectName("rtpd_stat_key")
            v = QLabel("—")
            v.setObjectName(obj)
            v.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            return k, v

        pk, self.sv_processed = _pair("Processed", "rtpd_sv")
        rk, self.sv_remaining = _pair("Remaining", "rtpd_sv")
        sk, self.sv_speed     = _pair("Speed",     "rtpd_sv")
        ek, self.sv_eta       = _pair("ETA",       "rtpd_sv")
        lk, self.sv_elapsed   = _pair("Elapsed",   "rtpd_sv")

        sg.addWidget(pk,               0, 0); sg.addWidget(self.sv_processed, 0, 1)
        sg.addWidget(rk,               0, 2); sg.addWidget(self.sv_remaining, 0, 3)
        sg.addWidget(sk,               1, 0); sg.addWidget(self.sv_speed,     1, 1)
        sg.addWidget(ek,               1, 2); sg.addWidget(self.sv_eta,       1, 3)
        sg.addWidget(lk,               2, 0); sg.addWidget(self.sv_elapsed,   2, 1, 1, 3)
        stats_frame.setLayout(sg)
        layout.addWidget(stats_frame)

        layout.addStretch()

        # Cancel / Close button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.action_btn = QPushButton("✕  Cancel")
        self.action_btn.setObjectName("rtpd_cancel_btn")
        self.action_btn.setMinimumWidth(120)
        self.action_btn.setMinimumHeight(36)
        self.action_btn.clicked.connect(self._on_btn_clicked)
        btn_row.addWidget(self.action_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)

        # QPropertyAnimation for smooth progress bar fill
        self._anim = QPropertyAnimation(self.progress_bar, b"value", self)
        self._anim.setDuration(250)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    # ── Timers ─────────────────────────────────────────────────────────────
    def _setup_timers(self):
        self._start_time = time.time()

        self._spin_timer = QTimer(self)
        self._spin_timer.setInterval(80)
        self._spin_timer.timeout.connect(self._tick_spinner)
        self._spin_timer.start()

        self._stats_timer = QTimer(self)
        self._stats_timer.setInterval(500)
        self._stats_timer.timeout.connect(self._refresh_stats)
        self._stats_timer.start()

    def _tick_spinner(self):
        self._spinner_idx = (self._spinner_idx + 1) % len(_SPINNER_FRAMES)
        self.spinner_lbl.setText(_SPINNER_FRAMES[self._spinner_idx])

    def _refresh_stats(self):
        if not self._start_time:
            return
        elapsed = time.time() - self._start_time
        self.sv_elapsed.setText(f"{elapsed:.0f}s")
        if self._total_files > 0:
            self.sv_processed.setText(str(self._files_processed))
            remaining = max(0, self._total_files - self._files_processed)
            self.sv_remaining.setText(str(remaining))
            if elapsed > 1 and self._files_processed > 0:
                speed = self._files_processed / elapsed
                self.sv_speed.setText(f"{speed:.1f} f/s")
                if remaining > 0:
                    self.sv_eta.setText(f"~{remaining / speed:.0f}s")
                else:
                    self.sv_eta.setText("done")

    # ── Public slots ───────────────────────────────────────────────────────
    @pyqtSlot(int, str)
    def update_progress(self, value, message):
        """Update progress bar (animated) and status text."""
        self._anim.stop()
        self._anim.setStartValue(self.progress_bar.value())
        self._anim.setEndValue(min(value, 100))
        self._anim.start()
        self.pct_lbl.setText(f"{value}%")
        self.status_lbl.setText(message)

    @pyqtSlot(str, int, int)
    def update_file(self, filename, current, total):
        """Update current-file label and internal counters for stats."""
        self._files_processed = current
        self._total_files = total
        short = (filename[:44] + "…") if len(filename) > 47 else filename
        self.file_lbl.setText(f"📄 {short}  ({current + 1} of {total})")

    def set_complete(self, message="✅ Complete!"):
        """Transition dialog to completion state."""
        self._is_processing = False
        self._spin_timer.stop()
        self._stats_timer.stop()
        self._refresh_stats()
        self.spinner_lbl.setText("✓")
        self.spinner_lbl.setStyleSheet(
            f"color: {'#4ADE80' if self._dark else '#16a34a'}; font-size: 18px;"
        )
        self.status_lbl.setText(message)
        self.file_lbl.setText("")
        self.action_btn.setText("✓  Close")
        self.action_btn.setObjectName("rtpd_close_btn")
        self.action_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1,
                    stop:0 #22C55E, stop:1 #15803D);
                color: white; border: none; border-radius: 8px;
                padding: 8px 24px; font-weight: 700; font-size: 12px;
            }
            QPushButton:hover {
                background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1,
                    stop:0 #4ADE80, stop:1 #22C55E);
            }
        """)

    def set_cancelled(self):
        """Transition dialog to cancelled state."""
        self._is_processing = False
        self._spin_timer.stop()
        self._stats_timer.stop()
        self.spinner_lbl.setText("✗")
        self.status_lbl.setText("Cancelled.")
        self.file_lbl.setText("")
        self.action_btn.setText("✗  Close")
        self.action_btn.setEnabled(True)

    def set_error(self, message):
        """Transition dialog to error state."""
        self._is_processing = False
        self._spin_timer.stop()
        self._stats_timer.stop()
        self.spinner_lbl.setText("✗")
        self.status_lbl.setText(f"Error: {message}")
        self.file_lbl.setText("")
        self.action_btn.setText("✗  Close")
        self.action_btn.setEnabled(True)

    # ── Internal ───────────────────────────────────────────────────────────
    def _on_btn_clicked(self):
        if self._is_processing:
            self._is_processing = False
            self.action_btn.setEnabled(False)
            self.status_lbl.setText("Cancelling…")
            self.cancelled.emit()
        else:
            self.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and not self._is_processing:
            self.accept()
        else:
            super().keyPressEvent(event)

    # ── Theme ──────────────────────────────────────────────────────────────
    def _apply_theme(self):
        dark = self._dark
        bg        = "#222222" if dark else "#f8f8f8"
        text_c    = "#E8E8E8" if dark else "#222222"
        sub_c     = "#909090" if dark else "#555555"
        bar_bg    = "#333333" if dark else "#e0e0e0"
        sep_c     = "#3a3a3a" if dark else "#e8d841"
        frame_bg  = "#2a2a2a" if dark else "#f0f0f0"
        frame_bdr = "#3a3a3a" if dark else "#dddddd"
        bar_end   = "#0ea5e9" if dark else "#f59e0b"
        btn_bg    = "#3a3a3a" if dark else "#e0e0e0"
        btn_fg    = "#f87171" if dark else "#dc2626"
        btn_bdr   = "#555555" if dark else "#cccccc"
        file_c    = "#60a5fa" if dark else "#2563eb"

        self.setStyleSheet(f"""
            QDialog {{
                background: {bg};
            }}
            QLabel {{
                background: transparent;
                color: {text_c};
            }}
            QLabel#rtpd_title {{
                font-weight: 700;
                font-size: 13px;
            }}
            QLabel#rtpd_spinner {{
                color: {'#4ADE80' if not dark else '#22C55E'};
            }}
            QLabel#rtpd_status {{
                color: {sub_c};
                font-size: 11px;
            }}
            QLabel#rtpd_file {{
                color: {file_c};
                font-size: 11px;
                font-weight: 600;
            }}
            QLabel#rtpd_pct {{
                font-weight: 700;
                font-size: 11px;
                color: {text_c};
            }}
            QLabel#rtpd_stat_key {{
                color: {sub_c};
                font-size: 10px;
            }}
            QLabel#rtpd_sv {{
                color: {text_c};
                font-size: 10px;
                font-weight: 600;
            }}
            QFrame#rtpd_sep {{
                background: {sep_c};
                max-height: 2px;
                border: none;
                margin: 1px 0px;
            }}
            QFrame#rtpd_stats_frame {{
                background: {frame_bg};
                border: 1px solid {frame_bdr};
                border-radius: 8px;
            }}
            QProgressBar#rtpd_bar {{
                background: {bar_bg};
                border: none;
                border-radius: 8px;
                min-height: 22px;
            }}
            QProgressBar#rtpd_bar::chunk {{
                background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:0,
                    stop:0 #22C55E, stop:0.55 #16a34a, stop:1 {bar_end});
                border-radius: 8px;
            }}
            QPushButton#rtpd_cancel_btn {{
                background: {btn_bg};
                color: {btn_fg};
                border: 1px solid {btn_bdr};
                border-radius: 8px;
                padding: 8px 24px;
                font-weight: 700;
                font-size: 12px;
            }}
            QPushButton#rtpd_cancel_btn:hover {{
                background: {'#ef4444' if dark else '#fecaca'};
                color: {'white' if dark else '#991b1b'};
                border: 1px solid #ef4444;
            }}
            QPushButton#rtpd_cancel_btn:disabled {{
                background: {'#2a2a2a' if dark else '#f0f0f0'};
                color: {'#555' if dark else '#aaa'};
            }}
        """)


class FolderNamingDialog(QDialog):
    """
    Modal dialog for naming the parent organization folder (e.g. CH_Org1).

    Shows a validated text field pre-filled with the auto-generated default
    name.  The primary "Organize" button stays disabled until the name passes
    all validation rules.
    """

    _INVALID_RE = re.compile(r'[/\\:*?"<>|]')

    def __init__(self, parent=None, default_name="CH_Org1",
                 target_dir="", dark=False):
        super().__init__(parent)
        self.default_name = default_name
        self.target_dir = target_dir
        self.dark = dark
        self._accepted_name = None

        self.setWindowTitle("Name Your Music Organization")
        # Scale dialog relative to screen
        screen = QDesktopWidget().availableGeometry(self)
        dlg_w = max(440, min(560, int(screen.width() * 0.35)))
        dlg_h = max(260, min(340, int(screen.height() * 0.38)))
        self.setMinimumSize(400, 240)
        self.resize(dlg_w, dlg_h)
        self.setModal(True)
        self.setWindowFlags(
            Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint
        )

        self._build_ui()
        self._apply_theme()

        if parent:
            pr = parent.geometry()
            self.move(
                pr.center().x() - self.width() // 2,
                pr.center().y() - self.height() // 2,
            )

    def _build_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(24, 20, 24, 18)

        title_lbl = QLabel("Organize Your Music Library")
        title_lbl.setFont(QFont("Inter", 14, QFont.Bold))
        title_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_lbl)

        subtitle_lbl = QLabel("Choose a name for this organized collection")
        subtitle_lbl.setObjectName("fnd_subtitle")
        subtitle_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_lbl)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("fnd_sep")
        layout.addWidget(sep)

        name_lbl = QLabel("Folder Name:")
        name_lbl.setObjectName("fnd_name_lbl")
        layout.addWidget(name_lbl)

        input_row = QHBoxLayout()
        self.name_input = QLineEdit(self.default_name)
        self.name_input.setMaxLength(50)
        self.name_input.setMinimumHeight(38)
        self.name_input.textChanged.connect(self._validate)
        input_row.addWidget(self.name_input)
        self.char_counter = QLabel(f"{len(self.default_name)}/50")
        self.char_counter.setObjectName("fnd_counter")
        self.char_counter.setMinimumWidth(48)
        self.char_counter.setAlignment(Qt.AlignCenter)
        input_row.addWidget(self.char_counter)
        layout.addLayout(input_row)

        self.validation_msg = QLabel("")
        self.validation_msg.setObjectName("fnd_vmsg")
        self.validation_msg.setMinimumHeight(18)
        layout.addWidget(self.validation_msg)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.reset_btn = QPushButton("↺ Reset to Default")
        self.reset_btn.setObjectName("fnd_reset_btn")
        self.reset_btn.setMaximumWidth(150)
        self.reset_btn.clicked.connect(self._reset_to_default)
        self.reset_btn.setVisible(False)
        btn_row.addWidget(self.reset_btn)
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("fnd_cancel_btn")
        cancel_btn.setMinimumWidth(90)
        cancel_btn.setMinimumHeight(36)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        self.organize_btn = QPushButton("⊞  Organize")
        self.organize_btn.setObjectName("fnd_ok_btn")
        self.organize_btn.setMinimumWidth(120)
        self.organize_btn.setMinimumHeight(36)
        self.organize_btn.setDefault(True)
        self.organize_btn.clicked.connect(self._on_organize_clicked)
        btn_row.addWidget(self.organize_btn)

        layout.addLayout(btn_row)
        self.setLayout(layout)
        self._validate(self.default_name)

    def _validate(self, text):
        raw  = text or ""
        name = raw.strip()
        self.char_counter.setText(f"{len(raw)}/50")
        self.char_counter.setStyleSheet(
            f"QLabel#fnd_counter {{ font-size: 10px; color: "
            f"{'#f59e0b' if len(raw) > 40 else ('#888' if not self.dark else '#aaa')}; }}"
        )
        self.reset_btn.setVisible(raw != self.default_name)

        if not name:
            self._set_msg("⚠  Please enter a folder name", "#f59e0b")
            self.organize_btn.setEnabled(False); return
        if self._INVALID_RE.search(name):
            self._set_msg("✗  Use letters, numbers, hyphens, underscores, spaces", "#e74c3c")
            self.organize_btn.setEnabled(False); return
        if len(name) > 50:
            self._set_msg("✗  Name too long (max 50 characters)", "#e74c3c")
            self.organize_btn.setEnabled(False); return
        if name[0] in (' ', '.'):
            self._set_msg("✗  Name cannot start with a space or dot", "#e74c3c")
            self.organize_btn.setEnabled(False); return
        if self.target_dir and (Path(self.target_dir) / name).exists():
            self._set_msg(f'✗  Folder "{name}" already exists', "#e74c3c")
            self.organize_btn.setEnabled(False); return

        self._set_msg("✓  Ready to organize", "#22C55E")
        self.organize_btn.setEnabled(True)

    def _set_msg(self, text, color):
        self.validation_msg.setText(text)
        self.validation_msg.setStyleSheet(
            f"QLabel#fnd_vmsg {{ font-size: 10px; color: {color}; min-height: 18px; }}"
        )

    def _reset_to_default(self):
        self.name_input.setText(self.default_name)
        self.name_input.selectAll()
        self.name_input.setFocus()

    def _on_organize_clicked(self):
        name = self.name_input.text().strip()
        if name:
            self._accepted_name = name
            self.accept()

    def get_folder_name(self):
        return self._accepted_name

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if self.organize_btn.isEnabled():
                self._on_organize_clicked()
        elif event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.name_input.selectAll()
        self.name_input.setFocus()

    def _apply_theme(self):
        dark = self.dark
        bg        = "#222222" if dark else "#f8f8f8"
        text_c    = "#E8E8E8" if dark else "#333333"
        sub_c     = "#909090" if dark else "#666666"
        input_bg  = "#2a2a2a" if dark else "white"
        input_bdr = "#444444" if dark else "#cccccc"
        sep_c     = "#3a3a3a" if dark else "#e8d841"
        can_bg    = "#3a3a3a" if dark else "#e0e0e0"
        can_fg    = "#E0E0E0" if dark else "#333333"
        can_bdr   = "#555555" if dark else "#bbbbbb"
        focus_bdr = "#4A90E2" if dark else "#ff9500"
        focus_bg  = "#1a2530" if dark else "#fffef5"
        reset_c   = "#60a5fa" if dark else "#3B82F6"
        self.setStyleSheet(f"""
            QDialog {{ background: {bg}; }}
            QLabel {{ color: {text_c}; background: transparent; }}
            QLabel#fnd_subtitle {{ color: {sub_c}; font-size: 11px; }}
            QLabel#fnd_name_lbl {{ font-weight: 700; font-size: 12px; }}
            QFrame#fnd_sep {{ background: {sep_c}; max-height: 2px; border: none; margin: 2px 0; }}
            QLineEdit {{
                background: {input_bg}; color: {text_c};
                border: 2px solid {input_bdr}; border-radius: 8px;
                padding: 8px 12px; font-size: 13px;
            }}
            QLineEdit:focus {{ border: 2px solid {focus_bdr}; background: {focus_bg}; }}
            QPushButton#fnd_ok_btn {{
                background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1,
                    stop:0 #22C55E, stop:1 #15803D);
                color: white; border: none; border-radius: 8px;
                padding: 8px 18px; font-weight: 700; font-size: 12px;
            }}
            QPushButton#fnd_ok_btn:hover {{
                background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1,
                    stop:0 #4ADE80, stop:1 #22C55E);
            }}
            QPushButton#fnd_ok_btn:disabled {{
                background: {'#3a3a3a' if dark else '#cccccc'};
                color: {'#666' if dark else '#999'};
            }}
            QPushButton#fnd_cancel_btn {{
                background: {can_bg}; color: {can_fg};
                border: 1px solid {can_bdr}; border-radius: 8px;
                padding: 8px 18px; font-weight: 600; font-size: 12px;
            }}
            QPushButton#fnd_cancel_btn:hover {{
                background: {'#4a4a4a' if dark else '#d0d0d0'};
            }}
            QPushButton#fnd_reset_btn {{
                background: transparent; color: {reset_c};
                border: none; font-size: 11px; padding: 4px 6px;
                text-decoration: underline;
            }}
        """)


class AnalysisWorker(QThread):
    """Worker thread para análise sem bloquear UI"""
    finished = pyqtSignal()
    result = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)
    file_tick = pyqtSignal(str, int, int)
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
    
    def run(self):
        try:
            fname = os.path.basename(self.file_path)
            self.file_tick.emit(fname, 0, 1)
            self.progress.emit(10, f"Analyzing: {fname}")
            result = analyze_track(self.file_path)
            self.progress.emit(90, "Formatting results…")
            self.result.emit(result)
            self.progress.emit(100, "Analysis complete!")
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit()


class OrganizationWorker(QThread):
    """Worker thread para organização de arquivos sem bloquear UI"""
    finished  = pyqtSignal()
    result    = pyqtSignal(dict)
    error     = pyqtSignal(str)
    progress  = pyqtSignal(int, str)   # 0-100, message
    file_tick = pyqtSignal(str, int, int)  # filename, idx, total

    def __init__(self, input_dir, output_dir, move_files=False,
                 parent_folder_name=None):
        super().__init__()
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.move_files = move_files
        self.parent_folder_name = parent_folder_name
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            self.progress.emit(5, "Searching for audio files…")
            audio_files = find_audio_files(self.input_dir)
            total = len(audio_files)
            self.progress.emit(10, f"Found {total} audio files")

            def _cb(filename, idx, total_f):
                self.file_tick.emit(filename, idx, total_f)
                pct = 10 + int((idx / max(total_f, 1)) * 85)
                self.progress.emit(pct, f"Processing: {filename}")
                return self._cancelled  # True → cancel loop

            result = organize_by_key(
                self.input_dir,
                self.output_dir,
                move_files=self.move_files,
                parent_folder_name=self.parent_folder_name,
                progress_callback=_cb,
            )
            self.progress.emit(98, "Finalizing…")
            self.result.emit(result)
            self.progress.emit(100, "Complete!")
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit()


class PlaylistWorker(QThread):
    """Worker thread para criação de playlists sem bloquear UI"""
    finished  = pyqtSignal()
    result    = pyqtSignal(dict)
    error     = pyqtSignal(str)
    progress  = pyqtSignal(int, str)
    file_tick = pyqtSignal(str, int, int)

    def __init__(self, playlist_fn, *args, **kwargs):
        super().__init__()
        self.playlist_fn = playlist_fn
        self.args = args
        self.kwargs = kwargs
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        try:
            self.progress.emit(5, "Starting playlist creation…")

            def _cb(filename, idx, total):
                self.file_tick.emit(filename, idx, total)
                pct = 5 + int((idx / max(total, 1)) * 88)
                self.progress.emit(pct, f"Analyzing: {filename}")
                return self._cancelled

            self.kwargs['progress_callback'] = _cb
            result = self.playlist_fn(*self.args, **self.kwargs)
            self.progress.emit(98, "Finalizing…")
            self.result.emit({'result': result})
            self.progress.emit(100, "Complete!")
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit()


class TransitionWorker(QThread):
    """Worker thread for transition comparison (compatibility tab)."""
    finished  = pyqtSignal()
    result    = pyqtSignal(dict)
    error     = pyqtSignal(str)
    progress  = pyqtSignal(int, str)
    file_tick = pyqtSignal(str, int, int)

    def __init__(self, file1, file2):
        super().__init__()
        self.file1 = file1
        self.file2 = file2

    def run(self):
        try:
            f1_name = os.path.basename(self.file1)
            f2_name = os.path.basename(self.file2)
            self.progress.emit(10, f"Analyzing: {f1_name}")
            self.file_tick.emit(f1_name, 0, 2)
            track1 = analyze_track(self.file1)
            self.progress.emit(55, f"Analyzing: {f2_name}")
            self.file_tick.emit(f2_name, 1, 2)
            track2 = analyze_track(self.file2)
            self.progress.emit(85, "Calculating compatibility scores…")
            transition = calculate_transition_score(track1, track2)
            self.progress.emit(100, "Analysis complete!")
            self.result.emit({
                'track1': track1, 'track2': track2, 'transition': transition
            })
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit()


class WaveformWorker(QThread):
    """Loads audio and computes waveform envelope + transition markers."""
    waveform_ready = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, file_path, n_bars=300):
        super().__init__()
        self.file_path = file_path
        self.n_bars = n_bars

    def run(self):
        try:
            import librosa
            import numpy as np
            y, sr = librosa.load(self.file_path, sr=22050, duration=None)
            # Compute RMS envelope using librosa (full track)
            frame_length = max(512, 2 * (len(y) // self.n_bars))
            hop_length = max(1, len(y) // self.n_bars)
            rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
            # Resample to exact n_bars
            if len(rms) > self.n_bars:
                indices = np.linspace(0, len(rms) - 1, self.n_bars).astype(int)
                bars = rms[indices]
            else:
                bars = rms
            # Normalize to 0-1
            peak = np.max(bars) if len(bars) > 0 else 1.0
            if peak > 0:
                bars = bars / peak
            # Mild compression (sqrt) so quieter parts are more visible
            bars = np.sqrt(bars)
            bars = [float(b) for b in bars[:self.n_bars]]

            # Detect transition points via spectral flux on chroma
            hop_chroma = 512
            chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_chroma)
            # Compute chroma flux (frame-to-frame distance)
            diff = np.sum(np.abs(np.diff(chroma, axis=1)), axis=0)
            # Map flux frames to bar indices
            n_flux = len(diff)
            n_bars_actual = len(bars)
            flux_per_bar = np.zeros(n_bars_actual)
            for i, v in enumerate(diff):
                idx = int(i * n_bars_actual / n_flux)
                if idx < n_bars_actual:
                    flux_per_bar[idx] = max(flux_per_bar[idx], v)

            # Thresholds: key transitions (".") = top 5%, sub-key ("-") = top 15%
            sorted_flux = np.sort(flux_per_bar[flux_per_bar > 0])
            if len(sorted_flux) > 0:
                key_thresh = np.percentile(sorted_flux, 95)
                sub_thresh = np.percentile(sorted_flux, 85)
            else:
                key_thresh = sub_thresh = float('inf')

            key_points = []   # bar indices for "."
            sub_points = []   # bar indices for "-"
            min_gap = max(3, n_bars_actual // 50)
            last_mark = -min_gap
            for i, v in enumerate(flux_per_bar):
                if i - last_mark < min_gap:
                    continue
                if v >= key_thresh:
                    key_points.append(i)
                    last_mark = i
                elif v >= sub_thresh:
                    sub_points.append(i)
                    last_mark = i

            self.waveform_ready.emit({
                'bars': bars,
                'key_points': key_points,
                'sub_points': sub_points,
            })
        except Exception as e:
            self.error.emit(str(e))


class WaveformWidget(QWidget):
    """Lightweight waveform display using QPainter — centered/mirrored."""

    def __init__(self, label="", color="#1DB954", parent=None):
        super().__init__(parent)
        self._bars = []
        self._key_points = []
        self._sub_points = []
        self._label = label
        self._color = QColor(color)
        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_data(self, data):
        if isinstance(data, dict):
            self._bars = data.get('bars', [])
            self._key_points = data.get('key_points', [])
            self._sub_points = data.get('sub_points', [])
        else:
            self._bars = data
        self.update()

    def set_label(self, text):
        self._label = text
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor(20, 20, 20, 200))

        # Label at top-left
        label_h = 18
        if self._label:
            painter.setPen(QColor(200, 200, 200))
            painter.setFont(QFont("Inter", 9, QFont.Bold))
            painter.drawText(8, 14, self._label)

        if not self._bars:
            painter.setPen(QColor(120, 120, 120))
            painter.setFont(QFont("Inter", 10))
            painter.drawText(self.rect(), Qt.AlignCenter, "Awaiting analysis...")
            painter.end()
            return

        # Marker row sits between label and waveform
        marker_y = label_h + 2
        marker_h = 12
        wave_top = marker_y + marker_h
        wave_bottom = h - 4
        draw_h = wave_bottom - wave_top
        if draw_h < 10:
            painter.end()
            return

        center_y = wave_top + draw_h / 2.0
        n = len(self._bars)
        bar_w = max(1.0, w / n)
        half_h = draw_h / 2.0

        # Draw center line
        painter.setPen(QColor(80, 80, 80))
        painter.drawLine(0, int(center_y), w, int(center_y))

        # Draw mirrored bars
        for i, amp in enumerate(self._bars):
            arm = max(1, int(amp * half_h))
            x = int(i * bar_w)
            bw = max(1, int(bar_w) - 1)
            c = QColor(self._color)
            c.setAlpha(160 + int(amp * 95))
            # Upper half (grows up from center)
            painter.fillRect(x, int(center_y) - arm, bw, arm, c)
            # Lower half (grows down from center)
            c2 = QColor(self._color)
            c2.setAlpha(120 + int(amp * 70))
            painter.fillRect(x, int(center_y), bw, arm, c2)

        # Draw key transition markers "." above waveform
        marker_font = QFont("Inter", 10, QFont.Bold)
        painter.setFont(marker_font)
        for idx in self._key_points:
            if 0 <= idx < n:
                mx = int(idx * bar_w + bar_w / 2)
                painter.setPen(QColor(255, 200, 50))
                painter.drawText(mx - 3, marker_y + marker_h - 1, ".")

        # Draw sub-key transition markers "-" above waveform
        for idx in self._sub_points:
            if 0 <= idx < n:
                mx = int(idx * bar_w + bar_w / 2)
                painter.setPen(QColor(180, 180, 180))
                painter.drawText(mx - 3, marker_y + marker_h - 1, "-")

        painter.end()


# Palm tree SVG silhouette – gradient fills for depth and richness
_PALM_TREE_SVG = b"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 160 280'>
  <defs>
    <linearGradient id='tg' x1='0' y1='0' x2='1' y2='0'>
      <stop offset='0%' stop-color='#0d3320'/>
      <stop offset='100%' stop-color='#2d6e45'/>
    </linearGradient>
    <linearGradient id='lg' x1='0' y1='1' x2='1' y2='0'>
      <stop offset='0%' stop-color='#0a2918'/>
      <stop offset='55%' stop-color='#1a4d2e'/>
      <stop offset='100%' stop-color='#3e7d3e'/>
    </linearGradient>
    <linearGradient id='lg2' x1='1' y1='0' x2='0' y2='1'>
      <stop offset='0%' stop-color='#2e5e1a'/>
      <stop offset='100%' stop-color='#1a4d2e'/>
    </linearGradient>
  </defs>
  <g>
    <path fill='url(#tg)' d='M74,280 C72,250 70,215 68,185 C66,155 68,125 66,100 C65,80 63,58 61,30 L67,27 C70,55 73,78 74,99 C76,125 75,155 77,185 C79,215 80,250 82,280 Z'/>
    <path fill='url(#lg)'  d='M64,32 Q2,-18 -20,20 Q22,2 62,50 Z'/>
    <path fill='url(#lg2)' d='M64,32 Q22,-12 14,30 Q38,12 62,50 Z'/>
    <path fill='url(#lg)'  d='M64,32 Q40,2 36,38 Q50,18 63,47 Z'/>
    <path fill='url(#lg2)' d='M64,32 Q65,5 68,32 Q66,18 67,42 Z'/>
    <path fill='url(#lg)'  d='M64,32 Q86,2 92,38 Q76,18 65,47 Z'/>
    <path fill='url(#lg2)' d='M64,32 Q108,-8 118,30 Q90,12 65,50 Z'/>
    <path fill='url(#lg)'  d='M64,32 Q142,-15 162,20 Q122,4 65,50 Z'/>
    <ellipse fill='#0d3320' cx='63' cy='46' rx='4' ry='3.5'/>
    <ellipse fill='#1a4d2e' cx='69' cy='48' rx='4' ry='3.5'/>
    <ellipse fill='#0d3320' cx='57' cy='48' rx='3.5' ry='3'/>
  </g>
</svg>"""


# Dromedary camel silhouette — FILLCOLOR is substituted at render time
_CAMEL_SVG_TMPL = (
    b"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 260 220'>"
    b"<g fill='FILLCOLOR'>"
    b"<rect x='166' y='153' width='13' height='57' rx='6'/>"
    b"<rect x='185' y='157' width='13' height='53' rx='6'/>"
    b"<rect x='60'  y='153' width='13' height='57' rx='6'/>"
    b"<rect x='79'  y='157' width='13' height='53' rx='6'/>"
    b"<ellipse cx='130' cy='144' rx='84' ry='42'/>"
    b"<ellipse cx='96'  cy='97'  rx='30' ry='54' transform='rotate(-7 96 97)'/>"
    b"<ellipse cx='58'  cy='147' rx='22' ry='20'/>"
    b"<ellipse cx='198' cy='137' rx='27' ry='23'/>"
    b"<path d='M 42,147 Q 30,115 38,80 Q 46,76 63,78 Q 60,115 56,147 Z'/>"
    b"<ellipse cx='31' cy='68' rx='26' ry='21'/>"
    b"<ellipse cx='12' cy='77' rx='15' ry='10'/>"
    b"<ellipse cx='8'  cy='72' rx='9'  ry='7'/>"
    b"<ellipse cx='48' cy='50' rx='7'  ry='12' transform='rotate(-28 48 50)'/>"
    b"<path d='M 222,125 Q 246,110 242,132 Q 240,143 229,140'"
    b" stroke='FILLCOLOR' stroke-width='7' fill='none' stroke-linecap='round'/>"
    b"</g></svg>"
)


class TropicalBackground(QWidget):
    """Tab widget with subtle shaded palm tree silhouettes as background decoration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._svg_renderer = QSvgRenderer(_PALM_TREE_SVG)
        self._dark = False

    def set_dark(self, dark: bool):
        self._dark = dark
        self.setStyleSheet(
            "QWidget { background: #1a1a1a; }" if dark
            else "QWidget { background: #dcdcdc; }"
        )
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if not self._svg_renderer.isValid():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        w, h = float(self.width()), float(self.height())
        svg_w, svg_h = 160.0, 280.0

        # Layer 1: distant background palm — top-center-right, very faint
        bg_scale = min(h * 0.28, 140.0) / svg_h
        bg_w, bg_h = svg_w * bg_scale, svg_h * bg_scale
        painter.save()
        painter.setOpacity(0.07)
        painter.translate(w * 0.55, 0.0)
        self._svg_renderer.render(painter, QRectF(0.0, 0.0, bg_w, bg_h))
        painter.restore()

        # Layer 2: foreground right palm — bottom-right, stronger (~52% height)
        desired_h = min(h * 0.52, 265.0)
        scale = desired_h / svg_h
        render_w = svg_w * scale
        painter.save()
        painter.setOpacity(0.26)
        painter.translate(w - render_w + 22.0, h - desired_h)
        self._svg_renderer.render(painter, QRectF(0.0, 0.0, render_w, desired_h))
        painter.restore()

        # Layer 3: mid-layer left palm — bottom-left, mirrored
        small_scale = scale * 0.62
        small_w = svg_w * small_scale
        small_h = svg_h * small_scale
        painter.save()
        painter.setOpacity(0.17)
        painter.translate(-8.0, h - small_h)
        painter.scale(-1.0, 1.0)
        painter.translate(-small_w, 0.0)
        self._svg_renderer.render(painter, QRectF(0.0, 0.0, small_w, small_h))
        painter.restore()

        painter.end()


class ThemeToggleSwitch(QWidget):
    """Compact pill toggle switch  ☀ day / 🌙 night."""
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dark = False
        self.setFixedSize(52, 28)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Toggle night mode")

    def is_dark(self) -> bool:
        return self._dark

    def set_dark(self, dark: bool, emit: bool = True):
        changed = (self._dark != dark)
        self._dark = dark
        if changed:
            self.update()
        if emit:
            self.toggled.emit(dark)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.set_dark(not self._dark)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = float(self.width()), float(self.height())
        # Pill background
        pill = QPainterPath()
        pill.addRoundedRect(QRectF(0, 0, w, h), h / 2, h / 2)
        painter.fillPath(pill, QColor("#2d2d2d" if self._dark else "#d0d0d0"))
        painter.setPen(QColor("#555" if self._dark else "#bbb"))
        painter.drawPath(pill)
        # Toggle circle
        mg = 3.0
        cd = h - 2 * mg
        cx = (w - mg - cd) if self._dark else mg
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#3d6ea0" if self._dark else "#F6C300"))
        painter.drawEllipse(QRectF(cx, mg, cd, cd))
        # Icon (sun / moon)
        icon = "\U0001f319" if self._dark else "\u2600"
        f = QFont()
        f.setPixelSize(int(cd * 0.65))
        painter.setFont(f)
        painter.setPen(QColor("#dde8f4" if self._dark else "#5a4000"))
        painter.drawText(QRectF(cx, mg, cd, cd), Qt.AlignCenter, icon)
        painter.end()


class DJAnalyzerGUI(QMainWindow):
    """Classe principal da interface gráfica com PyQt5 - CAMEL-HOT Theme"""
    
    def __init__(self, language='ENG'):
        super().__init__()
        self.translator = Translator(language)
        self.tips_manager = DJTipsManager(language)
        self.selected_file = None
        self.selected_input_folder = None
        self.selected_output_folder = None
        self.analysis_results = []
        self._dark: bool = False
        self._cards: list = []
        self._outputs: list = []
        self._tab_roots: list = []
        self._browse_buttons: list = []  # Browse buttons for theme-aware styling
        self._header_widgets: list = []  # Widgets to exclude from color remapping
        self._footer_widgets: list = []  # Widgets to exclude from color remapping
        # Worker threads and progress dialogs
        self.analysis_worker = None
        self.organization_worker = None
        self.playlist_worker = None
        self.progress_dialog = None
        _s = QSettings("CamelHot", "DJAnalyzer")
        self._dark = _s.value("darkMode", False, type=bool)
        self.apply_theme(self._dark)
        self.init_ui()
    
    def apply_theme(self, dark: bool = False):
        """Applies day or night theme to content area. Header/footer use inline styles."""
        # Desert sunset gradient colors from logo
        # Green (left) -> Yellow -> Orange -> Red/Brown (right)
        stylesheet = """
        QMainWindow {
            background: qlineargradient(
                spread:pad, x1:0 y1:0, x2:1 y2:0,
                stop:0 #1a4d2e,
                stop:0.25 #3d6e40,
                stop:0.4 #f4d03f,
                stop:0.65 #ff9500,
                stop:0.85 #f07c1e,
                stop:1 #c1440e
            );
        }
        
        QWidget {
            background: transparent;
            color: #191414;
        }
        
        QLabel {
            min-height: 16px;
        }
        
        #central_widget {
            background: rgba(26, 77, 46, 0.1);
        }
        
        QTabWidget {
            background: #dcdcdc;
            border-radius: 12px;
        }
        
        QTabWidget::pane {
            border: 3px solid #e8d841;
            background: #dcdcdc;
            border-radius: 12px;
            margin-top: -2px;
        }
        
        QTabBar::tab {
            background: linear-gradient(180deg, #f8f9fa 0%, #f1f3f4 100%);
            color: #2d3748;
            padding: 12px 28px;
            margin: 2px 2px 0px 2px;
            border-radius: 12px 12px 0px 0px;
            font-weight: 700;
            font-size: 13px;
            border: 1px solid rgba(232,216,65,0.3);
            border-bottom: none;
            letter-spacing: 0.4px;
            font-family: 'Inter', 'Roboto', 'Open Sans', sans-serif;
            min-width: 80px;
            text-align: center;
        }
        
        QTabBar::tab:selected {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:0,
                stop:0 #1a6b3c, stop:0.65 #2d8a52, stop:1 #c8a820);
            color: white;
            border: 1px solid #c8a820;
            border-bottom: 3px solid #e8d841;
            font-weight: 700;
            font-size: 12px;
        }
        
        QTabBar::tab:hover:!selected {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1,
                stop:0 #f8f8f4, stop:1 #eeebe2);
            color: #ff9500;
            border: 1px solid rgba(255,149,0,0.5);
        }
        
        QPushButton {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1,
                stop:0 #22C55E, stop:1 #15803D);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 18px;
            font-weight: 600;
            font-size: 12px;
            font-family: 'Inter', 'Roboto', 'Open Sans', sans-serif;
            letter-spacing: 0.3px;
        }
        
        QPushButton:focus { outline: none; }
        
        QLineEdit QPushButton, QLineEdit > QPushButton,
        QWidget > QLineEdit + QPushButton {
            color: #1a1a1a;
            background: #f0f0f0;
            border: 1px solid #ddd;
        }
        
        QLineEdit QPushButton:hover, QWidget > QLineEdit + QPushButton:hover {
            background: #e0e0e0;
            border: 1px solid #bbb;
        }
        
        QLineEdit {
            background: white;
            color: #222222;
            border: 1px solid #cccccc;
            border-radius: 10px;
            padding: 12px 16px;
            font-size: 13px;
            font-family: 'Inter', 'Roboto', 'Open Sans', sans-serif;
            font-weight: 500;
        }
        
        QLineEdit:focus {
            border: 2px solid #4A90E2;
            background: #fffef5;
        }
        
        QLineEdit:read-only {
            background: #f5f5f5;
            color: #666666;
            border: 1px solid #e0e0e0;
        }
        
        QLineEdit:disabled {
            background: #f0f0f0;
            color: #999999;
            border: 1px solid #e8e8e8;
        }
        
        QTextEdit {
            background: white;
            color: #222222;
            border: 1px solid #cccccc;
            border-radius: 10px;
            padding: 12px 16px;
            font-size: 12px;
            font-family: 'Courier New', monospace;
            line-height: 1.6;
            font-weight: 400;
        }
        
        QTextEdit:focus {
            border: 2px solid #4A90E2;
            background: #fffef5;
        }
        
        QTextEdit:read-only {
            background: #f5f5f5;
            color: #666666;
        }
        
        QTextEdit:disabled {
            background: #f0f0f0;
            color: #999999;
        }
        
        QComboBox {
            background: white;
            color: #222222;
            border: 2px solid #cccccc;
            border-radius: 8px;
            padding: 6px 8px;
            font-size: 11px;
            font-family: 'Segoe UI', 'Roboto', sans-serif;
            font-weight: 500;
            min-height: 18px;
        }
        
        QComboBox:hover {
            border: 2px solid #4A90E2;
            background: #fffef5;
        }
        
        QComboBox:focus {
            border: 2px solid #4A90E2;
        }
        
        QComboBox:read-only {
            background: #f5f5f5;
            color: #666666;
        }
        
        QComboBox:disabled {
            background: #f0f0f0;
            color: #999999;
            border: 2px solid #e8e8e8;
        }
        
        QComboBox::drop-down {
            border: none;
            background: transparent;
            width: 20px;
            margin-right: 4px;
        }
        
        QComboBox::down-arrow {
            image: none;
            width: 14px;
            height: 14px;
        }
        
        QComboBox QAbstractItemView {
            background: white;
            color: #222222;
            border: 1px solid #cccccc;
            border-radius: 6px;
            selection-background-color: #1DB954;
            selection-color: #ffffff;
            outline: none;
            padding: 4px;
        }
        
        QComboBox QAbstractItemView::item {
            padding: 6px 10px;
            min-height: 26px;
            font-weight: 600;
            color: #222222;
            background: white;
        }
        
        QComboBox QAbstractItemView::item:hover {
            background: #e8f0ff;
            color: #222222;
        }
        
        QComboBox QAbstractItemView::item:selected {
            background: #1DB954;
            color: #ffffff;
        }
        
        QSpinBox {
            background: white;
            color: #222222;
            border: 2px solid #cccccc;
            border-radius: 8px;
            padding: 6px 8px;
            font-size: 11px;
            font-family: 'Segoe UI', 'Roboto', sans-serif;
            font-weight: 500;
            min-height: 18px;
        }
        
        QSpinBox:focus {
            border: 2px solid #4A90E2;
        }
        
        QSpinBox:read-only {
            background: #f5f5f5;
            color: #666666;
            border: 2px solid #e0e0e0;
        }
        
        QSpinBox:disabled {
            background: #f0f0f0;
            color: #999999;
        }
        
        QCheckBox {
            color: #444444;
            font-weight: 600;
            spacing: 8px;
            font-family: 'Segoe UI', 'Roboto', sans-serif;
        }
        
        QCheckBox:disabled {
            color: #999999;
        }
        
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border-radius: 4px;
            border: 2px solid #e8d841;
        }
        
        QCheckBox::indicator:checked {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1, stop:0 #1DB954, stop:1 #ff9500);
            border: 2px solid #ff9500;
        }
        
        QLabel {
            color: #444444;
            font-weight: 500;
        }
        
        QLabel:disabled {
            color: #999999;
        }
        
        QFrame {
            background: transparent;
            border: 1px solid rgba(232,216,65,0.2);
            border-radius: 8px;
        }
        
        QRadioButton {
            color: #444444;
            font-weight: 500;
            spacing: 6px;
        }
        
        QRadioButton:disabled {
            color: #999999;
        }
        
        QRadioButton::indicator {
            width: 16px;
            height: 16px;
            border-radius: 8px;
            border: 2px solid #e8d841;
        }
        
        QRadioButton::indicator:checked {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1, stop:0 #1DB954, stop:1 #ff9500);
            border: 2px solid #ff9500;
        }
        
        QMessageBox {
            background: qlineargradient(
                spread:pad, x1:0 y1:0, x2:1 y2:1,
                stop:0 #f8f8f8,
                stop:1 #f0f0f0
            );
        }
        
        QMessageBox QLabel {
            color: #191414;
        }
        
        QDialog {
            background: qlineargradient(
                spread:pad, x1:0 y1:0, x2:1 y2:1,
                stop:0 #f8f8f8,
                stop:1 #f0f0f0
            );
        }
        
        QDialog QLabel {
            color: #191414;
        }
        
        QDialog QLineEdit {
            background: white;
            color: #191414;
            border: 2px solid #e8d841;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 11px;
        }
        
        QDialog QLineEdit:focus {
            border: 2px solid #ff9500;
            background: #fffef5;
        }
        
        QDialog QPushButton {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1, stop:0 #1DB954, stop:1 #16a844);
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 600;
            font-size: 10px;
            min-width: 70px;
        }
        
        QDialog QPushButton:hover {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1, stop:0 #1ed760, stop:1 #1aa34a);
        }
        
        QDialog QPushButton:pressed {
            background: #1aa34a;
        }
        """

        night = """
        QMainWindow {
            background: qlineargradient(
                spread:pad, x1:0 y1:0, x2:1 y2:0,
                stop:0 #1a4d2e, stop:0.25 #3d6e40, stop:0.4 #f4d03f,
                stop:0.65 #ff9500, stop:0.85 #f07c1e, stop:1 #c1440e
            );
        }
        QWidget { background: transparent; color: #E0E0E0; }
        #central_widget { background: rgba(26, 77, 46, 0.1); }
        QTabWidget { background: #1a1a1a; border-radius: 12px; }
        QTabWidget::pane {
            border: 3px solid #2a4a3a;
            background: #1a1a1a;
            border-radius: 12px;
            margin-top: -2px;
        }
        QTabBar::tab {
            background: #252525;
            color: #c2ccd8;
            padding: 12px 28px;
            margin: 2px 2px 0px 2px;
            border-radius: 12px 12px 0px 0px;
            font-weight: 700; font-size: 13px;
            border: 1px solid rgba(255,255,255,0.08);
            border-bottom: none;
            letter-spacing: 0.4px;
            font-family: 'Inter', 'Roboto', 'Open Sans', sans-serif;
            min-width: 80px; text-align: center;
        }
        QTabBar::tab:selected {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:0,
                stop:0 #1a6b3c, stop:0.65 #2d8a52, stop:1 #c8a820);
            color: white;
            border: 1px solid #c8a820;
            border-bottom: 3px solid #e8d841;
            font-weight: 700; font-size: 12px;
        }
        QTabBar::tab:hover:!selected {
            background: #2d2d2d;
            color: #b0b8c8;
            border: 1px solid rgba(255,255,255,0.14);
        }
        QPushButton {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1,
                stop:0 #22C55E, stop:1 #15803D);
            color: white; border: none; border-radius: 8px;
            padding: 8px 18px; font-weight: 600; font-size: 12px;
            font-family: 'Inter', 'Roboto', 'Open Sans', sans-serif;
            letter-spacing: 0.3px;
        }
        QPushButton:hover {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1,
                stop:0 #4ADE80, stop:1 #22C55E);
            border: 1px solid rgba(74,222,128,0.4);
        }
        QPushButton:pressed { background: #166534; }
        QLineEdit {
            background: #1e1e1e; color: #E8E8E8;
            border: 1px solid #333333; border-radius: 10px;
            padding: 12px 16px; font-size: 13px;
            font-family: 'Inter', 'Roboto', 'Open Sans', sans-serif;
            font-weight: 500;
        }
        QLineEdit:focus { 
            border: 2px solid #4A90E2; 
            background: #252525; 
        }
        QLineEdit:read-only {
            background: #1a1a1a;
            color: #888888;
            border: 1px solid #2a2a2a;
        }
        QLineEdit:disabled {
            background: #1a1a1a;
            color: #555555;
            border: 1px solid #2a2a2a;
        }
        QTextEdit {
            background: #1e1e1e; color: #d0e8d0;
            border: 1px solid #333333; border-radius: 10px;
            padding: 12px 16px; font-size: 12px;
            font-family: 'Courier New', monospace; line-height: 1.6;
        }
        QTextEdit:focus {
            border: 2px solid #4A90E2;
            background: #252525;
        }
        QTextEdit:read-only {
            background: #1a1a1a;
            color: #888888;
        }
        QTextEdit:disabled {
            background: #1a1a1a;
            color: #555555;
        }
        QComboBox {
            background: #1e1e1e; color: #E8E8E8;
            border: 2px solid #444444; border-radius: 8px;
            padding: 6px 8px; font-size: 11px;
            font-family: 'Segoe UI', 'Roboto', sans-serif;
            font-weight: 500;
            min-height: 18px;
        }
        QComboBox:hover { 
            border: 2px solid #4A90E2;
            background: #252525;
        }
        QComboBox:focus {
            border: 2px solid #4A90E2;
        }
        QComboBox:read-only {
            background: #1a1a1a;
            color: #888888;
        }
        QComboBox:disabled {
            background: #1a1a1a;
            color: #555555;
            border: 2px solid #2a2a2a;
        }
        QComboBox::drop-down { 
            border: none; 
            background: transparent; 
            width: 20px;
            margin-right: 4px;
        }
        QComboBox::down-arrow {
            image: none;
            width: 14px;
            height: 14px;
        }
        QComboBox QAbstractItemView {
            background: #1e1e1e; color: #E8E8E8;
            border: 1px solid #444444; border-radius: 6px;
            selection-background-color: #1DB954;
            selection-color: #ffffff;
            outline: none;
            padding: 4px;
        }
        QComboBox QAbstractItemView::item {
            padding: 6px 10px; min-height: 26px; font-weight: 600;
            color: #E8E8E8; background: #1e1e1e;
        }
        QComboBox QAbstractItemView::item:hover {
            background: #2d5a4a; color: #E8E8E8;
        }
        QComboBox QAbstractItemView::item:selected {
            background: #1DB954; color: #ffffff;
        }
        QSpinBox {
            background: #1e1e1e; color: #E8E8E8;
            border: 2px solid #444444; border-radius: 8px;
            padding: 6px 8px; font-size: 11px;
            font-family: 'Segoe UI', 'Roboto', sans-serif;
            font-weight: 500;
            min-height: 18px;
        }
        QSpinBox:focus {
            border: 2px solid #4A90E2;
            background: #252525;
        }
        QSpinBox:read-only {
            background: #1a1a1a;
            color: #888888;
            border: 2px solid #2a2a2a;
        }
        QSpinBox:disabled {
            background: #1a1a1a;
            color: #555555;
            border: 2px solid #2a2a2a;
        }
        QCheckBox { 
            color: #E8E8E8; 
            font-weight: 600; 
            spacing: 8px; 
        }
        QCheckBox:disabled {
            color: #666666;
        }
        QCheckBox::indicator {
            width: 18px; height: 18px; border-radius: 4px;
            border: 2px solid #444444;
        }
        QCheckBox::indicator:checked {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1,
                stop:0 #1DB954, stop:1 #ff9500);
            border: 2px solid #ff9500;
        }
        QLabel { 
            color: #E8E8E8;
            font-weight: 500;
            min-height: 16px;
        }
        QLabel:disabled {
            color: #666666;
        }
        QFrame {
            background: transparent;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px;
        }
        QRadioButton { 
            color: #E8E8E8; 
            font-weight: 500; 
            spacing: 6px; 
        }
        QRadioButton:disabled {
            color: #666666;
        }
        QRadioButton::indicator {
            width: 16px; height: 16px; border-radius: 8px;
            border: 2px solid #444444;
        }
        QRadioButton::indicator:checked {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1,
                stop:0 #1DB954, stop:1 #ff9500);
            border: 2px solid #ff9500;
        }
        QScrollBar:vertical {
            background: #1a1a1a; width: 8px; border-radius: 4px; margin: 0px;
        }
        QScrollBar::handle:vertical {
            background: #404040; border-radius: 4px; min-height: 24px;
        }
        QScrollBar::handle:vertical:hover { background: #606060; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        QScrollBar:horizontal {
            background: #1a1a1a; height: 8px; border-radius: 4px; margin: 0px;
        }
        QScrollBar::handle:horizontal {
            background: #404040; border-radius: 4px; min-width: 24px;
        }
        QScrollBar::handle:horizontal:hover { background: #606060; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
        QScrollArea { border: none; background: transparent; }
        QMessageBox { background: #1e1e1e; }
        QMessageBox QLabel { color: #E0E0E0; }
        QDialog { background: #1e1e1e; }
        QDialog QLabel { color: #E0E0E0; }
        QDialog QLineEdit {
            background: #1e1e1e; color: #E0E0E0;
            border: 2px solid #444444; border-radius: 6px;
            padding: 8px 12px; font-size: 11px;
        }
        QDialog QLineEdit:focus { border: 2px solid #4A90E2; background: #1a2530; }
        QDialog QPushButton {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1,
                stop:0 #1DB954, stop:1 #16a844);
            color: white; border: none; border-radius: 6px;
            padding: 8px 16px; font-weight: 600; font-size: 10px; min-width: 70px;
        }
        QDialog QPushButton:hover {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1,
                stop:0 #1ed760, stop:1 #1aa34a);
        }
        QDialog QPushButton:pressed { background: #1aa34a; }
        """

        self.setStyleSheet(night if dark else stylesheet)
        
        # Apply FIXED dark background - outer border stays dark/black (never changes)
        # This allows the central TropicalBackground and tabs to show properly
        # without the outer surround changing colors
        palette = QPalette()
        palette.setColor(QPalette.Background, QColor("#0a0a0a"))  # Nearly black - stays fixed
        self.setPalette(palette)
        self.setAutoFillBackground(True)
    
    def _style_browse_button(self, button):
        """Apply theme-appropriate styling to browse buttons"""
        if self._dark:
            button.setStyleSheet("""
                QPushButton {
                    background: #2d2d2d;
                    color: #E0E0E0;
                    border: 1px solid #444444;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: 600;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #3d3d3d;
                    border: 1px solid #666666;
                }
                QPushButton:pressed {
                    background: #1d1d1d;
                }
            """)
        else:
            button.setStyleSheet("""
                QPushButton {
                    background: #f0f0f0;
                    color: #1a1a1a;
                    border: 1px solid #ddd;
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: 600;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: #e0e0e0;
                    border: 1px solid #bbb;
                }
                QPushButton:pressed {
                    background: #d0d0d0;
                }
            """)
    
    def get_file_dialog_stylesheet(self):
        """Retorna stylesheet para diálogos de arquivo com tema desert sunset"""
        return """
        QFileDialog {
            background: qlineargradient(
                spread:pad, x1:0 y1:0, x2:1 y2:1,
                stop:0 #f8f8f8,
                stop:1 #f0f0f0
            );
        }
        
        QFileDialog QWidget {
            background: transparent;
            color: #191414;
        }
        
        QFileDialog QLabel {
            color: #191414;
            font-weight: 600;
        }
        
        QFileDialog QLineEdit {
            background: white;
            color: #191414;
            border: 2px solid #e8d841;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 11px;
        }
        
        QFileDialog QLineEdit:focus {
            border: 2px solid #ff9500;
            background: #fffef5;
        }
        
        QFileDialog QPushButton {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1, stop:0 #1DB954, stop:1 #16a844);
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 600;
            font-size: 10px;
            min-width: 70px;
        }
        
        QFileDialog QPushButton:hover {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1, stop:0 #1ed760, stop:1 #1aa34a);
        }
        
        QFileDialog QPushButton:pressed {
            background: #1aa34a;
        }
        
        QFileDialog QComboBox {
            background: white;
            color: #191414;
            border: 2px solid #e8d841;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 10px;
        }
        
        QFileDialog QComboBox:hover {
            border: 2px solid #ff9500;
        }
        
        QFileDialog QListView {
            background: white;
            color: #191414;
            border: 1px solid #ddd;
            border-radius: 4px;
            outline: none;
        }
        
        QFileDialog QListView::item:selected {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1, stop:0 #1DB954, stop:1 #ff9500);
            color: white;
        }
        
        QFileDialog QListView::item:hover {
            background: #f0f0f0;
        }
        
        QFileDialog QTreeView {
            background: white;
            color: #191414;
            border: 1px solid #ddd;
            border-radius: 4px;
            outline: none;
        }
        
        QFileDialog QTreeView::item:selected {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1, stop:0 #1DB954, stop:1 #ff9500);
            color: white;
        }
        
        QFileDialog QTreeView::item:hover {
            background: #f0f0f0;
        }
        
        QFileDialog QHeaderView::section {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1, stop:0 #f4d03f, stop:1 #ff9500);
            color: #191414;
            padding: 6px;
            border: 1px solid #e8d841;
            font-weight: 600;
        }
        
        QFileDialog QCheckBox {
            color: #191414;
            spacing: 6px;
        }
        
        QFileDialog QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 2px solid #e8d841;
            border-radius: 3px;
        }
        
        QFileDialog QCheckBox::indicator:checked {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1, stop:0 #1DB954, stop:1 #ff9500);
            border: 2px solid #ff9500;
        }
        """
    
    def init_ui(self):
        """Inicializa a interface do usuário"""
        self.setWindowTitle(self.translator.get('window_title'))
        # Scale initial geometry to screen – occupy ~80 % of available area
        screen = QDesktopWidget().availableGeometry(self)
        win_w = max(860, min(1400, int(screen.width() * 0.80)))
        win_h = max(560, min(1000, int(screen.height() * 0.80)))
        x = screen.x() + (screen.width()  - win_w) // 2
        y = screen.y() + (screen.height() - win_h) // 2
        self.setGeometry(x, y, win_w, win_h)

        # Allow window to be resizable with a sensible minimum
        self.setMinimumSize(760, 480)
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        
        # Widget central
        central_widget = QWidget()
        central_widget.setObjectName("central_widget")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)
        
        # Header com logo profissional
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        
        # Logo container - supports SVG and image formats (size scales with window)
        logo_container = QWidget()
        logo_layout = QVBoxLayout()
        logo_layout.setContentsMargins(0, 0, 0, 0)
        _logo_sz = max(72, min(110, int(win_w * 0.10)))

        assets_dir = get_assets_dir()
        logo_found = False
        
        # Try to load image formats first (PNG, JPG), then SVG
        for logo_name in ["camel_mascot.png", "camel_mascot.jpg", "camel_mascot.jpeg", "camel_mascot.svg"]:
            logo_path = assets_dir / logo_name
            if logo_path.exists():
                if logo_name.endswith(".svg"):
                    logo_svg = QSvgWidget(str(logo_path))
                    logo_svg.setMinimumSize(_logo_sz, _logo_sz)
                    logo_svg.setMaximumSize(_logo_sz, _logo_sz)
                    logo_layout.addWidget(logo_svg)
                else:
                    logo_pixmap = QPixmap(str(logo_path))
                    logo_pixmap = logo_pixmap.scaledToWidth(_logo_sz, Qt.SmoothTransformation)
                    logo_label = QLabel()
                    logo_label.setPixmap(logo_pixmap)
                    logo_label.setAlignment(Qt.AlignCenter)
                    logo_layout.addWidget(logo_label)
                logo_found = True
                break
        
        if not logo_found:
            # Placeholder if no logo found
            placeholder = QLabel("🐪")
            _ph_pt = max(28, min(48, int(_logo_sz * 0.45)))
            placeholder_font = QFont("Inter", _ph_pt)
            placeholder.setFont(placeholder_font)
            placeholder.setAlignment(Qt.AlignCenter)
            logo_layout.addWidget(placeholder)
        
        logo_container.setLayout(logo_layout)
        logo_container.setStyleSheet("""
            background: rgba(255, 255, 255, 0.95);
            border: 3px solid #e8d841;
            border-radius: 12px;
            padding: 10px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        """)
        header_layout.addWidget(logo_container)
        
        # Título principal CAMEL-HOT com estilo do logo
        title_widget = QWidget()
        title_layout = QVBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(2)
        
        # Main title with gradient effect — font scales with window width
        title = QLabel("CAMEL-HOT")
        _title_pt = max(24, min(42, int(win_w * 0.043)))
        title_font = QFont("Inter", _title_pt, QFont.Bold)
        title_font.setLetterSpacing(QFont.PercentageSpacing, 110)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Split color effect: CAMEL in green, HOT in orange
        title.setStyleSheet(f"""
            QLabel {{
                background: transparent;
                color: #1a4d2e;
                font-weight: 900;
                font-size: {_title_pt}px;
                letter-spacing: 3px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            }}
        """)
        self._header_widgets.append(title)  # Exclude from color remapping
        title_layout.addWidget(title)
        
        # Subtitle with style
        subtitle = QLabel(self.translator.get('subtitle'))
        subtitle_font = QFont("Inter", 11, QFont.Bold)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignLeft)
        subtitle.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #ff9500;
                font-weight: 600;
                letter-spacing: 1px;
            }
        """)
        self._header_widgets.append(subtitle)  # Exclude from color remapping
        title_layout.addWidget(subtitle)
        
        # Tagline
        tagline = QLabel(self.translator.get('tagline'))
        tagline_font = QFont("Inter", 9)
        tagline_font.setItalic(True)
        tagline.setFont(tagline_font)
        tagline.setAlignment(Qt.AlignLeft)
        tagline.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #1DB954;
                font-style: italic;
                font-size: 9px;
            }
        """)
        self._header_widgets.append(tagline)  # Exclude from color remapping
        title_layout.addWidget(tagline)
        
        title_widget.setLayout(title_layout)
        title_widget.setStyleSheet("background: transparent;")
        header_layout.addWidget(title_widget)
        header_layout.addStretch()

        # Right-side controls: theme toggle stacked above language selector
        right_controls = QWidget()
        right_controls.setStyleSheet("background: transparent;")
        right_vbox = QVBoxLayout()
        right_vbox.setContentsMargins(0, 0, 0, 0)
        right_vbox.setSpacing(6)

        # Theme toggle (top-right, above language selector)
        toggle_row = QHBoxLayout()
        toggle_row.setContentsMargins(0, 0, 0, 0)
        toggle_row.addStretch()
        self._theme_toggle = ThemeToggleSwitch()
        self._theme_toggle.set_dark(self._dark, emit=False)
        self._theme_toggle.toggled.connect(self.toggle_dark_mode)
        toggle_row.addWidget(self._theme_toggle)
        right_vbox.addLayout(toggle_row)

        # Language Selector Button
        lang_selector = QComboBox()
        lang_selector.addItems(['English (ENG)', 'Português (PT)', 'Español (ES)'])
        lang_selector.setMaximumWidth(160)
        lang_selector.setCurrentIndex(0 if self.translator.get_current_language() == 'ENG' else
                                      1 if self.translator.get_current_language() == 'PT' else 2)
        lang_selector.currentIndexChanged.connect(self.change_language)
        lang_selector.setStyleSheet("""
            QComboBox {
                background: white;
                color: #191414;
                border: 2px solid #e8d841;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 10px;
                font-weight: 600;
            }
            QComboBox:hover {
                border: 2px solid #ff9500;
            }
        """)
        right_vbox.addWidget(lang_selector)
        right_controls.setLayout(right_vbox)
        header_layout.addWidget(right_controls)

        main_layout.addLayout(header_layout)
        
        # Linha decorativa com gradient (desert sunset colors)
        sep_line = QFrame()
        sep_line.setFrameShape(QFrame.HLine)
        sep_line.setStyleSheet("""
            background: qlineargradient(
                spread:pad, x1:0 y1:0, x2:1 y2:0,
                stop:0 #1a4d2e,
                stop:0.25 #3d6e40,
                stop:0.4 #f4d03f,
                stop:0.65 #ff9500,
                stop:0.85 #f07c1e,
                stop:1 #c1440e
            );
            height: 3px;
            border: none;
            margin: 10px 0px 10px 0px;
        """)
        main_layout.addWidget(sep_line)
        main_layout.addSpacing(4)
        
        # Tabs — icon-prefixed labels for DJ identity
        self.tabs = tabs = QTabWidget()
        tabs.setDocumentMode(False)
        tabs.addTab(self.create_analyze_tab(),        "⬣ " + self.translator.get('tab_analyze'))
        tabs.addTab(self.create_organize_tab(),       "⊞ " + self.translator.get('tab_organize'))
        tabs.addTab(self.create_playlist_tab(),       "♫ " + self.translator.get('tab_playlist'))
        tabs.addTab(self.create_compatibility_tab(),  "⇌ " + self.translator.get('tab_compatibility'))
        tabs.addTab(self.create_tips_tab(),           "★ " + self.translator.get('tab_tips'))
        tabs.addTab(self.create_camelot_wheel_tab(),  "◎ Camelot Wheel")
        tabs.addTab(self.create_about_tab(),          "ℹ " + self.translator.get('tab_about'))
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #c8a820;
                border-radius: 0px 8px 8px 8px;
            }
            QTabBar {
                background: transparent;
            }
        """)

        # Context-sensitive action buttons in the tab bar corner
        corner = self._create_tab_corner_widget()
        tabs.setCornerWidget(corner, Qt.TopRightCorner)
        tabs.currentChanged.connect(corner.stack.setCurrentIndex)

        main_layout.addWidget(tabs, 1)
        
        # Footer container with background styling
        footer_container = QWidget()
        footer_container.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    spread:pad, x1:0 y1:0, x2:1 y2:0,
                    stop:0 #1a4d2e,
                    stop:0.25 #3d6e40,
                    stop:0.4 #f4d03f,
                    stop:0.65 #ff9500,
                    stop:0.85 #f07c1e,
                    stop:1 #c1440e
                );
                border-top: 2px solid #e8d841;
            }
        """)
        
        # Rodapé com botão sair (desert sunset styled)
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(15, 10, 15, 10)
        footer_layout.setSpacing(10)
        
        # Texto do rodapé em branco para bom contraste
        footer_text = QLabel(self.translator.get('footer_text'))
        footer_text.setStyleSheet("color: #ffffff; font-weight: 500; font-size: 11px; letter-spacing: 0.3px; background: transparent;")
        self._footer_widgets.append(footer_text)  # Mark for exclusion from color remapping
        footer_layout.addWidget(footer_text)
        
        # Developer signature on the right
        developer_sig = QLabel("Design by H.Gwedez")
        developer_sig.setStyleSheet("color: #e8d841; font-weight: 500; font-size: 10px; font-style: italic; background: transparent;")
        self._footer_widgets.append(developer_sig)  # Mark for exclusion from color remapping
        footer_layout.addStretch()
        footer_layout.addWidget(developer_sig)
        footer_layout.addSpacing(20)
        
        exit_btn = QPushButton(self.translator.get('btn_exit'))
        exit_btn.setMaximumWidth(110)
        exit_btn.setMaximumHeight(36)
        exit_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    spread:pad, x1:0 y1:0, x2:1 y2:1,
                    stop:0 #ff9500,
                    stop:1 #c1440e
                );
                color: white;
                border: 2px solid #f07c1e;
                border-radius: 10px;
                padding: 8px 20px;
                font-weight: 700;
                font-size: 11px;
                font-family: 'Segoe UI', 'Roboto', 'Inter', sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(
                    spread:pad, x1:0 y1:0, x2:1 y2:1,
                    stop:0 #ffaa25,
                    stop:1 #d95a2b
                );
                border: 2px solid #ffaa25;
            }
            QPushButton:pressed {
                background: qlineargradient(
                    spread:pad, x1:0 y1:0, x2:1 y2:1,
                    stop:0 #ff8800,
                    stop:1 #a83a0e
                );
            }
        """)
        exit_btn.clicked.connect(self.close)
        footer_layout.addWidget(exit_btn)
        
        footer_container.setLayout(footer_layout)
        main_layout.addWidget(footer_container, 0)

        central_widget.setLayout(main_layout)
        self._collect_styled_refs()
        self._refresh_content_styles()  # Always refresh to ensure proper colors

    def _create_tab_corner_widget(self):
        """Context-sensitive compact action buttons shown in the tab bar top-right corner."""

        def _btn(label, c1, c2, handler, min_w=100):
            b = QPushButton(label)
            b.setFixedHeight(34)
            b.setMinimumWidth(min_w)
            b.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            b.clicked.connect(handler)
            b.setStyleSheet(
                f"QPushButton {{"
                f"  background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1,"
                f"    stop:0 {c1}, stop:1 {c2});"
                f"  color: white; border: none; border-radius: 7px;"
                f"  padding: 4px 14px; font-weight: 700; font-size: 11px;"
                f"  letter-spacing: 0.3px; min-height: 26px;"
                f"}}"
                f"QPushButton:hover {{"
                f"  border: 1px solid rgba(255,255,255,0.45);"
                f"}}"
                f"QPushButton:pressed {{ padding-top: 5px; }}"
            )
            return b

        BLUE   = ("#3B82F6", "#1D4ED8")
        GREEN  = ("#22C55E", "#16A34A")
        AMBER  = ("#F59E0B", "#D97706")
        RED    = ("#EF4444", "#B91C1C")
        PURPLE = ("#8B5CF6", "#6D28D9")

        stack = QStackedWidget()
        stack.setStyleSheet("background: transparent;")
        stack.setMaximumHeight(44)

        def _page(*buttons):
            w = QWidget()
            w.setStyleSheet("background: transparent;")
            h = QHBoxLayout()
            h.setContentsMargins(4, 6, 8, 6)
            h.setSpacing(6)
            for b in buttons:
                h.addWidget(b)
            w.setLayout(h)
            stack.addWidget(w)

        # Tab 0 – Analyze
        _page(
            _btn("▶  Analyze", *BLUE, self.handle_analyze, 118),
            _btn("✕ Clear",   *RED,  self.clear_analyze_tab, 78),
        )
        # Tab 1 – Organize
        _page(
            _btn("⊞  Organize", *AMBER, self.handle_organize, 118),
            _btn("✕ Clear",     *RED,   self.clear_organize_tab, 78),
        )
        # Tab 2 – Playlist — sophisticated emerald-gold design
        pl_create = QPushButton("♫  Create Playlist")
        pl_create.setFixedHeight(34)
        pl_create.setMinimumWidth(148)
        pl_create.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        pl_create.clicked.connect(self.handle_playlist)
        pl_create.setStyleSheet("""
            QPushButton {
                background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:0,
                    stop:0 #1a6b3c, stop:0.55 #22C55E, stop:1 #c8a820);
                color: white; border: none; border-radius: 8px;
                padding: 4px 16px; font-weight: 800; font-size: 11px;
                letter-spacing: 0.6px; min-height: 26px;
            }
            QPushButton:hover {
                background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:0,
                    stop:0 #22C55E, stop:0.55 #4ADE80, stop:1 #e8d841);
                border: 1px solid rgba(232,216,65,0.6);
            }
            QPushButton:pressed {
                background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:0,
                    stop:0 #14532d, stop:1 #92400e);
            }
        """)
        pl_clear = QPushButton("✕ Clear")
        pl_clear.setFixedHeight(34)
        pl_clear.setMinimumWidth(78)
        pl_clear.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        pl_clear.clicked.connect(self.clear_playlist_tab)
        pl_clear.setStyleSheet("""
            QPushButton {
                background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1,
                    stop:0 #7f1d1d, stop:1 #450a0a);
                color: #fca5a5; border: 1px solid rgba(239,68,68,0.4);
                border-radius: 7px; padding: 4px 14px;
                font-weight: 700; font-size: 11px; min-height: 26px;
            }
            QPushButton:hover {
                background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1,
                    stop:0 #EF4444, stop:1 #B91C1C);
                color: white; border: 1px solid rgba(255,255,255,0.3);
            }
            QPushButton:pressed { background: #450a0a; }
        """)
        _page(pl_create, pl_clear)
        # Tab 3 – Compatibility
        _page(
            _btn("⇌ Compare",  *BLUE,  self.handle_transition_comparison, 102),
            _btn("◎ Check Key", *AMBER, self.handle_compatibility, 102),
            _btn("✕ Clear",    *RED,   lambda: self.compat_output.clear(), 78),
        )
        # Tab 4 – Tips
        _page(
            _btn("★  Next Tip", *PURPLE, self.show_next_tip, 108),
        )
        # Tab 5 – Camelot Wheel (informational, no actions)
        _page()
        # Tab 6 – About (informational, no actions)
        _page()

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        hl = QHBoxLayout()
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(stack)
        container.setLayout(hl)
        container.stack = stack          # expose for currentChanged signal
        return container

    def closeEvent(self, event):
        """Gracefully stop all running worker threads before closing."""
        workers = [
            getattr(self, 'analysis_worker', None),
            getattr(self, 'organization_worker', None),
            getattr(self, 'playlist_worker', None),
            getattr(self, 'transition_worker', None),
        ]
        for w in workers:
            if w is not None and w.isRunning():
                try:
                    if hasattr(w, 'cancel'):
                        w.cancel()
                    w.quit()
                    w.wait(2000)
                except Exception:
                    pass
        # Close any open progress dialog
        pd = getattr(self, '_progress_dialog', None)
        if pd is not None:
            try:
                pd.close()
            except Exception:
                pass
        event.accept()

    def toggle_dark_mode(self, dark: bool):
        """Switch day ↔ night theme and persist the choice."""
        self._dark = dark
        self.apply_theme(dark)
        self._collect_styled_refs()
        self._refresh_content_styles()
        QSettings("CamelHot", "DJAnalyzer").setValue("darkMode", dark)

    def _collect_styled_refs(self):
        """Collect widget refs for dynamic theme switching. Called after init_ui() completes."""
        self._tab_roots = []
        self._cards = []
        self._outputs = []
        self._browse_buttons = []
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, TropicalBackground):
                self._tab_roots.append(w)
        for root in self._tab_roots:
            for frame in root.findChildren(QFrame):
                ss = frame.styleSheet()
                # Match glass cards in either day mode or night mode form
                if 'rgba(255, 255, 255, 0.48)' in ss or 'rgba(36, 40, 48, 0.88)' in ss:
                    self._cards.append(frame)
            # Collect browse buttons (any QPushButton next to a QLineEdit with "Browse" text)
            for btn in root.findChildren(QPushButton):
                if 'Browse' in btn.text() or 'browse' in btn.text().lower():
                    self._browse_buttons.append(btn)
        for attr in ('analyze_output', 'org_output_text', 'pl_output_text', 'compat_output', '_about_info'):
            w = getattr(self, attr, None)
            if w is not None:
                self._outputs.append(w)

    def _refresh_content_styles(self):
        """Re-apply dynamic styles to inline-styled widgets after a theme toggle."""
        dark = self._dark
        # TropicalBackground fill
        for root in self._tab_roots:
            root.set_dark(dark)
        # Glass cards
        card_ss = (
            """
            QFrame {
                background: rgba(36, 40, 48, 0.88);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-top: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 12px; padding: 14px;
            }"""
            if dark else
            """
            QFrame {
                background: rgba(255, 255, 255, 0.48);
                border: 1px solid rgba(255, 255, 255, 0.72);
                border-top: 1px solid rgba(255, 255, 255, 0.90);
                border-radius: 12px; padding: 14px;
            }"""
        )
        for card in self._cards:
            card.setStyleSheet(card_ss)
        # Output QTextEdit widgets
        out_ss = (
            """
            QTextEdit {
                background: rgba(18, 22, 28, 0.92);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-top: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 12px; padding: 14px;
                font-size: 11px; font-family: 'Courier New', monospace;
                color: #d0e8d0;
            }"""
            if dark else
            """
            QTextEdit {
                background: rgba(255, 255, 255, 0.78);
                border: 1px solid rgba(255, 255, 255, 0.70);
                border-top: 1px solid rgba(255, 255, 255, 0.92);
                border-radius: 12px; padding: 14px;
                font-size: 11px; font-family: 'Courier New', monospace;
                color: #191414;
            }"""
        )
        for output in self._outputs:
            output.setStyleSheet(out_ss)
        # Browse buttons
        for btn in self._browse_buttons:
            self._style_browse_button(btn)
        # Camel silhouette colour
        if getattr(self, '_camel_label', None) is not None:
            self._camel_label.setPixmap(self._camel_pixmap(dark))
        # Update Camelot wheel tab sections (wheel, info, tips) based on theme
        for root in self._tab_roots:
            for frame in root.findChildren(QFrame):
                ss = frame.styleSheet()
                # Identify and update wheel section (yellow border #e8d841)
                if '#e8d841' in ss and 'd4a574' not in ss and '4ADE80' not in ss and '1DB954' not in ss:
                    frame.setStyleSheet("""
                        QFrame {
                            background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1,
                                stop:0 #2a2a2a,
                                stop:1 #1f1f1f
                            );
                            border: 3px solid #e8d841;
                            border-radius: 12px;
                            padding: 24px;
                        }
                    """ if dark else """
                        QFrame {
                            background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1,
                                stop:0 #f9fafb,
                                stop:1 #f3f4f6
                            );
                            border: 3px solid #e8d841;
                            border-radius: 12px;
                            padding: 24px;
                        }
                    """)
                # Identify and update info section (green border #4ADE80 or #1DB954)
                elif '#4ADE80' in ss or '#1DB954' in ss:
                    frame.setStyleSheet("""
                        QFrame {
                            background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1,
                                stop:0 #2a2a2a,
                                stop:1 #1f1f1f
                            );
                            border: 2px solid #4ADE80;
                            border-radius: 12px;
                            padding: 20px;
                        }
                    """ if dark else """
                        QFrame {
                            background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1,
                                stop:0 #f3f4f6,
                                stop:1 #f9fafb
                            );
                            border: 2px solid #1DB954;
                            border-radius: 12px;
                            padding: 20px;
                        }
                    """)
                # Identify and update tips section (tan border #d4a574 or #f4d03f)
                elif '#d4a574' in ss or '#f4d03f' in ss:
                    frame.setStyleSheet("""
                        QFrame {
                            background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1,
                                stop:0 #2a2a2a,
                                stop:1 #1f1f1f
                            );
                            border: 2px solid #d4a574;
                            border-radius: 12px;
                            padding: 20px;
                        }
                    """ if dark else """
                        QFrame {
                            background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1,
                                stop:0 #fff9e6,
                                stop:1 #fff3cc
                            );
                            border: 2px solid #f4d03f;
                            border-radius: 12px;
                            padding: 20px;
                        }
                    """)
        # Inline-colour labels inside tab roots — remap day ↔ night
        # EXCLUDING header and footer widgets (keep fixed colors)
        _to_night = {
            '#1a3d28': '#7fc49a',
            '#1DB954': '#4ADE80',
            '#191414': '#D0D0D0',
            '#1a4d2e': '#6db890',
            '#404654': '#9098b0',
            '#3B82F6': '#60a5fa',
            '#666':    '#a0a0a0',
            '#c0392b': '#e57373',
            '#000000': '#E0E0E0',
        }
        _to_day = {v: k for k, v in _to_night.items()}
        color_map = _to_night if dark else _to_day
        # Build set of widgets to exclude from color remapping
        excluded_widgets = set(self._header_widgets) if hasattr(self, '_header_widgets') else set()
        excluded_widgets.update(set(self._footer_widgets) if hasattr(self, '_footer_widgets') else set())
        for root in self._tab_roots:
            for w in root.findChildren(QLabel):
                # Skip header/footer widgets (keep fixed colors)
                if w in excluded_widgets:
                    continue
                ss = w.styleSheet()
                if not ss:
                    continue
                new_ss = ss
                for old, new in color_map.items():
                    new_ss = new_ss.replace(old, new)
                if new_ss != ss:
                    w.setStyleSheet(new_ss)

    def change_language(self, index):
        """Change application language and reload UI"""
        languages = ['ENG', 'PT', 'ES']
        new_language = languages[index]
        if self.translator.get_current_language() != new_language:
            self.translator.set_language(new_language)
            self.tips_manager.set_language(new_language)
            # Reload the entire UI
            central_widget = self.centralWidget()
            if central_widget is not None:
                central_widget.deleteLater()
            self.init_ui()
    
    def create_analyze_tab(self):
        """Cria aba para analisar música individual"""
        widget = TropicalBackground()
        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 16)

        # Title
        title = QLabel(self.translator.get('analyze_title'))
        title.setFont(QFont("Inter", 15, QFont.Bold))
        title.setStyleSheet("color: #1DB954; letter-spacing: 0.5px;")
        layout.addWidget(title)

        sep_line = QFrame()
        sep_line.setFrameShape(QFrame.HLine)
        sep_line.setStyleSheet("background: #e8d841; height: 2px; border: none; margin: 2px 0px 6px 0px;")
        layout.addWidget(sep_line)

        # INPUT SECTION — compact glass card
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.48);
                border: 1px solid rgba(255, 255, 255, 0.72);
                border-top: 1px solid rgba(255, 255, 255, 0.90);
                border-radius: 12px;
                padding: 14px;
            }
        """)
        input_layout = QVBoxLayout()
        input_layout.setSpacing(10)

        file_label = QLabel(self.translator.get('label_select_file'))
        file_label.setStyleSheet("font-weight: 700; color: #1a3d28; font-size: 12px; letter-spacing: 0.3px;")
        input_layout.addWidget(file_label)

        file_row = QHBoxLayout()
        self.analyze_file_input = QLineEdit()
        self.analyze_file_input.setReadOnly(True)
        self.analyze_file_input.setPlaceholderText(self.translator.get('placeholder_audio_file'))
        self.analyze_file_input.setMinimumHeight(36)
        file_row.addWidget(self.analyze_file_input)

        browse_btn = QPushButton(self.translator.get('btn_browse'))
        browse_btn.setMaximumWidth(100)
        browse_btn.setMinimumHeight(36)
        browse_btn.clicked.connect(self.browse_analyze_file)
        self._style_browse_button(browse_btn)
        file_row.addWidget(browse_btn)
        input_layout.addLayout(file_row)

        input_frame.setLayout(input_layout)
        layout.addWidget(input_frame)

        # RESULTS — label + maximized output text area
        res_label = QLabel(self.translator.get('label_results'))
        res_label.setStyleSheet(
            "font-weight: 700; color: #1a3d28; font-size: 12px;"
            " letter-spacing: 0.4px; padding-left: 2px; padding-top: 4px;"
        )
        layout.addWidget(res_label)

        self.analyze_output = QTextEdit()
        self.analyze_output.setReadOnly(True)
        self.analyze_output.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.78);
                border: 1px solid rgba(255, 255, 255, 0.70);
                border-top: 1px solid rgba(255, 255, 255, 0.92);
                border-radius: 12px;
                padding: 14px;
                font-size: 11px;
                font-family: 'Courier New', monospace;
            }
        """)
        self.analyze_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.analyze_output, 1)

        widget.setLayout(layout)
        return widget
    
    def create_organize_tab(self):
        """Cria aba para organizar biblioteca"""
        widget = TropicalBackground()
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(28, 28, 28, 28)

        # Title
        title = QLabel(self.translator.get('organize_title'))
        title_font = QFont("Inter", 16, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #1DB954; letter-spacing: 0.5px;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: #e8d841; height: 2px; border: none; margin: 4px 0px;")
        layout.addWidget(sep)

        # Folder selection card
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.48);
                border: 1px solid rgba(255, 255, 255, 0.72);
                border-top: 1px solid rgba(255, 255, 255, 0.90);
                border-radius: 12px;
                padding: 14px;
            }
        """)
        card_layout = QVBoxLayout()
        card_layout.setSpacing(14)

        # Input folder row
        input_label = QLabel(self.translator.get('label_input_folder'))
        input_label.setStyleSheet("font-weight: 700; color: #191414; font-size: 12px;")
        card_layout.addWidget(input_label)
        input_row = QHBoxLayout()
        self.org_input = QLineEdit()
        self.org_input.setReadOnly(True)
        self.org_input.setPlaceholderText(self.translator.get('placeholder_music_source'))
        self.org_input.setMinimumHeight(38)
        input_row.addWidget(self.org_input)
        browse_in = QPushButton(self.translator.get('btn_browse'))
        browse_in.setMaximumWidth(110)
        browse_in.setMinimumHeight(38)
        browse_in.clicked.connect(self.browse_org_input)
        self._style_browse_button(browse_in)
        input_row.addWidget(browse_in)
        card_layout.addLayout(input_row)

        # Output folder row
        output_label = QLabel(self.translator.get('label_output_folder'))
        output_label.setStyleSheet("font-weight: 700; color: #191414; font-size: 12px;")
        card_layout.addWidget(output_label)
        output_row = QHBoxLayout()
        self.org_output = QLineEdit()
        self.org_output.setReadOnly(True)
        self.org_output.setPlaceholderText(self.translator.get('placeholder_destination'))
        self.org_output.setMinimumHeight(38)
        output_row.addWidget(self.org_output)
        browse_out = QPushButton(self.translator.get('btn_browse'))
        browse_out.setMaximumWidth(110)
        browse_out.setMinimumHeight(38)
        browse_out.clicked.connect(self.browse_org_output)
        self._style_browse_button(browse_out)
        output_row.addWidget(browse_out)
        card_layout.addLayout(output_row)

        # Move checkbox
        self.move_files = QCheckBox(self.translator.get('checkbox_move_files'))
        card_layout.addWidget(self.move_files)
        warning = QLabel(self.translator.get('warning_move_files'))
        warning.setStyleSheet("color: #c0392b; font-size: 11px;")
        card_layout.addWidget(warning)
        card.setLayout(card_layout)
        layout.addWidget(card)

        # Progress / output area
        prog_label = QLabel(self.translator.get('label_progress'))
        prog_label.setStyleSheet(
            "font-weight: 700; color: #1a3d28; font-size: 12px;"
            " letter-spacing: 0.4px; padding-left: 2px; padding-top: 4px;"
        )
        layout.addWidget(prog_label)

        self.org_output_text = QTextEdit()
        self.org_output_text.setReadOnly(True)
        self.org_output_text.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.78);
                border: 1px solid rgba(255, 255, 255, 0.70);
                border-top: 1px solid rgba(255, 255, 255, 0.92);
                border-radius: 12px;
                padding: 14px;
                font-size: 11px;
                font-family: 'Courier New', monospace;
            }
        """)
        self.org_output_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.org_output_text, 1)

        widget.setLayout(layout)
        return widget
    
    def create_playlist_tab(self):
        """Cria aba para criar playlist"""
        widget = TropicalBackground()
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(28, 28, 28, 28)

        # Title
        title = QLabel(self.translator.get('playlist_title'))
        title_font = QFont("Inter", 16, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #1DB954; letter-spacing: 0.5px;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: #e8d841; height: 2px; border: none; margin: 4px 0px;")
        layout.addWidget(sep)

        # Options card
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.48);
                border: 1px solid rgba(255, 255, 255, 0.72);
                border-top: 1px solid rgba(255, 255, 255, 0.90);
                border-radius: 12px;
                padding: 14px;
            }
        """)
        card_layout = QVBoxLayout()
        card_layout.setSpacing(10)

        # Playlist mode — 2×2 grid so buttons don't clip
        mode_label = QLabel(self.translator.get('label_playlist_mode'))
        mode_label.setStyleSheet("font-weight: 700; color: #191414; font-size: 12px;")
        card_layout.addWidget(mode_label)

        self.pl_mode_group = QButtonGroup()
        mode_grid = QGridLayout()
        mode_grid.setSpacing(6)
        mode_simple = QRadioButton(self.translator.get('mode_simple_harmonic'))
        mode_sequence = QRadioButton(self.translator.get('mode_harmonic_sequence'))
        mode_transition = QRadioButton(self.translator.get('mode_key_transition'))
        mode_zone = QRadioButton(self.translator.get('mode_camelot_zone'))
        for rb in (mode_simple, mode_sequence, mode_transition, mode_zone):
            rb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.pl_mode_group.addButton(mode_simple, 0)
        self.pl_mode_group.addButton(mode_sequence, 1)
        self.pl_mode_group.addButton(mode_transition, 2)
        self.pl_mode_group.addButton(mode_zone, 3)
        mode_simple.setChecked(True)
        mode_grid.addWidget(mode_simple, 0, 0)
        mode_grid.addWidget(mode_sequence, 0, 1)
        mode_grid.addWidget(mode_transition, 1, 0)
        mode_grid.addWidget(mode_zone, 1, 1)
        card_layout.addLayout(mode_grid)

        # Music folder row
        folder_label = QLabel(self.translator.get('label_music_folder'))
        folder_label.setStyleSheet("font-weight: 700; color: #191414; font-size: 12px;")
        card_layout.addWidget(folder_label)
        folder_row = QHBoxLayout()
        self.pl_input = QLineEdit()
        self.pl_input.setReadOnly(True)
        self.pl_input.setPlaceholderText(self.translator.get('placeholder_select_music'))
        self.pl_input.setMinimumHeight(36)
        folder_row.addWidget(self.pl_input)
        browse_in = QPushButton(self.translator.get('btn_browse'))
        browse_in.setMaximumWidth(110)
        browse_in.setMinimumHeight(36)
        browse_in.clicked.connect(self.browse_pl_input)
        self._style_browse_button(browse_in)
        folder_row.addWidget(browse_in)
        card_layout.addLayout(folder_row)

        # Output filename row
        out_label = QLabel(self.translator.get('label_playlist_filename'))
        out_label.setStyleSheet("font-weight: 700; color: #191414; font-size: 12px;")
        card_layout.addWidget(out_label)
        out_row = QHBoxLayout()
        self.pl_output = QLineEdit("my_playlist.m3u")
        self.pl_output.setMinimumHeight(36)
        out_row.addWidget(self.pl_output)
        card_layout.addLayout(out_row)

        # --- Filters: Direction, BPM, Energy, Groove, Limit ---
        filter_label = QLabel("Filters:")
        filter_label.setStyleSheet("font-weight: 700; color: #191414; font-size: 12px;")
        card_layout.addWidget(filter_label)

        filter_grid = QGridLayout()
        filter_grid.setSpacing(8)
        filter_grid.setColumnStretch(1, 1)
        filter_grid.setColumnStretch(3, 1)
        filter_grid.setColumnStretch(5, 1)

        # Row 0: Direction, Energy, Groove
        dir_lbl = QLabel(self.translator.get('label_direction'))
        dir_lbl.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        filter_grid.addWidget(dir_lbl, 0, 0)
        self.pl_direction = QComboBox()
        self.pl_direction.addItems(["forward", "backward", "zigzag"])
        self.pl_direction.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        filter_grid.addWidget(self.pl_direction, 0, 1)

        energy_lbl = QLabel("Energy:")
        energy_lbl.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        filter_grid.addWidget(energy_lbl, 0, 2)
        self.pl_energy = QComboBox()
        self.pl_energy.addItems(["Any", "Low", "Medium", "High"])
        self.pl_energy.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        filter_grid.addWidget(self.pl_energy, 0, 3)

        groove_lbl = QLabel("Groove:")
        groove_lbl.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        filter_grid.addWidget(groove_lbl, 0, 4)
        self.pl_groove = QComboBox()
        self.pl_groove.addItems(["Any", "Driving", "Rolling", "Laid-back", "Swinging", "Syncopated"])
        self.pl_groove.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        filter_grid.addWidget(self.pl_groove, 0, 5)

        # Row 1: Min BPM, Max BPM, Limit
        min_bpm_lbl = QLabel(self.translator.get('label_min_bpm'))
        min_bpm_lbl.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        filter_grid.addWidget(min_bpm_lbl, 1, 0)
        self.pl_bpm_min = QSpinBox()
        self.pl_bpm_min.setMinimum(0)
        self.pl_bpm_min.setMaximum(300)
        self.pl_bpm_min.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        filter_grid.addWidget(self.pl_bpm_min, 1, 1)

        max_bpm_lbl = QLabel(self.translator.get('label_max_bpm'))
        max_bpm_lbl.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        filter_grid.addWidget(max_bpm_lbl, 1, 2)
        self.pl_bpm_max = QSpinBox()
        self.pl_bpm_max.setMinimum(0)
        self.pl_bpm_max.setMaximum(300)
        self.pl_bpm_max.setValue(300)
        self.pl_bpm_max.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        filter_grid.addWidget(self.pl_bpm_max, 1, 3)

        limit_lbl = QLabel("Limit:")
        limit_lbl.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        filter_grid.addWidget(limit_lbl, 1, 4)
        self.pl_limit = QSpinBox()
        self.pl_limit.setMinimum(1)
        self.pl_limit.setMaximum(1000)
        self.pl_limit.setValue(50)
        self.pl_limit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        filter_grid.addWidget(self.pl_limit, 1, 5)

        card_layout.addLayout(filter_grid)

        # Hidden combos — keep for handle_playlist defaults
        self.pl_key = QComboBox()
        self.pl_key.addItem("Any")
        self.pl_key.addItems(sorted(set(CAMELOT_MAP.values())))
        self.pl_key.hide()
        self.pl_seq_start = QComboBox()
        self.pl_seq_start.addItems(sorted(set(CAMELOT_MAP.values())))
        self.pl_seq_start.setCurrentText("8A")
        self.pl_seq_start.hide()
        self.pl_target_key = QComboBox()
        self.pl_target_key.addItems(sorted(set(CAMELOT_MAP.values())))
        self.pl_target_key.setCurrentText("3B")
        self.pl_target_key.hide()
        card.setLayout(card_layout)
        layout.addWidget(card)

        # Result label + expanding output
        res_pl_label = QLabel("Result:")
        res_pl_label.setStyleSheet(
            "font-weight: 700; color: #1a3d28; font-size: 12px;"
            " letter-spacing: 0.4px; padding-left: 2px; padding-top: 4px;"
        )
        layout.addWidget(res_pl_label)

        self.pl_output_text = QTextEdit()
        self.pl_output_text.setReadOnly(True)
        self.pl_output_text.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.78);
                border: 1px solid rgba(255, 255, 255, 0.70);
                border-top: 1px solid rgba(255, 255, 255, 0.92);
                border-radius: 12px;
                padding: 14px;
                font-size: 11px;
                font-family: 'Courier New', monospace;
            }
        """)
        self.pl_output_text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.pl_output_text, 1)

        widget.setLayout(layout)
        return widget
    
    def create_compatibility_tab(self):
        """Cria aba para verificar compatibilidade"""
        widget = TropicalBackground()
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(28, 28, 28, 28)

        # Title
        title = QLabel(self.translator.get('compatibility_title'))
        title_font = QFont("Inter", 16, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #1DB954; letter-spacing: 0.5px;")
        layout.addWidget(title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("background: #e8d841; height: 2px; border: none; margin: 4px 0px;")
        layout.addWidget(sep)

        # SECTION 1: Transition Comparison card
        sec1_card = QFrame()
        sec1_card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.48);
                border: 1px solid rgba(255, 255, 255, 0.72);
                border-top: 1px solid rgba(255, 255, 255, 0.90);
                border-radius: 12px;
                padding: 14px;
            }
        """)
        sec1_layout = QVBoxLayout()
        sec1_layout.setSpacing(10)
        sec1_title = QLabel("Transition Comparison")
        sec1_title.setStyleSheet("font-weight: 700; color: #3B82F6; font-size: 13px; letter-spacing: 0.3px;")
        sec1_layout.addWidget(sec1_title)

        file1_row = QHBoxLayout()
        file1_label = QLabel("Track 1:")
        file1_label.setStyleSheet("font-weight: 600; color: #191414; min-width: 60px;")
        file1_row.addWidget(file1_label)
        self.compat_file1 = QLineEdit()
        self.compat_file1.setReadOnly(True)
        self.compat_file1.setPlaceholderText("Choose first track...")
        self.compat_file1.setMinimumHeight(36)
        file1_row.addWidget(self.compat_file1)
        browse1_btn = QPushButton(self.translator.get('btn_browse'))
        browse1_btn.setMaximumWidth(90)
        browse1_btn.setMinimumHeight(36)
        browse1_btn.clicked.connect(self.browse_compat_file1)
        self._style_browse_button(browse1_btn)
        file1_row.addWidget(browse1_btn)
        sec1_layout.addLayout(file1_row)

        file2_row = QHBoxLayout()
        file2_label = QLabel("Track 2:")
        file2_label.setStyleSheet("font-weight: 600; color: #191414; min-width: 60px;")
        file2_row.addWidget(file2_label)
        self.compat_file2 = QLineEdit()
        self.compat_file2.setReadOnly(True)
        self.compat_file2.setPlaceholderText("Choose second track...")
        self.compat_file2.setMinimumHeight(36)
        file2_row.addWidget(self.compat_file2)
        browse2_btn = QPushButton(self.translator.get('btn_browse'))
        browse2_btn.setMaximumWidth(90)
        browse2_btn.setMinimumHeight(36)
        browse2_btn.clicked.connect(self.browse_compat_file2)
        self._style_browse_button(browse2_btn)
        file2_row.addWidget(browse2_btn)
        sec1_layout.addLayout(file2_row)
        sec1_card.setLayout(sec1_layout)
        sec1_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # SECTION 2: Camelot Key Compatibility card
        sec2_card = QFrame()
        sec2_card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.48);
                border: 1px solid rgba(255, 255, 255, 0.72);
                border-top: 1px solid rgba(255, 255, 255, 0.90);
                border-radius: 12px;
                padding: 14px;
            }
        """)
        sec2_layout = QVBoxLayout()
        sec2_layout.setSpacing(10)
        sec2_title = QLabel("Camelot Key Compatibility")
        sec2_title.setStyleSheet("font-weight: 700; color: #FF9500; font-size: 13px; letter-spacing: 0.3px;")
        sec2_layout.addWidget(sec2_title)

        key_row = QHBoxLayout()
        key_label = QLabel("Select Camelot Key:")
        key_label.setStyleSheet("font-weight: 600; color: #191414;")
        key_row.addWidget(key_label)
        self.compat_key = QComboBox()
        self.compat_key.addItems(sorted(set(CAMELOT_MAP.values())))
        self.compat_key.setCurrentText("8A")
        key_row.addWidget(self.compat_key)
        key_row.addStretch()
        sec2_layout.addLayout(key_row)
        sec2_card.setLayout(sec2_layout)
        sec2_card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Align both control cards side by side
        controls_row = QHBoxLayout()
        controls_row.setSpacing(18)
        controls_row.addWidget(sec1_card, 1)
        controls_row.addWidget(sec2_card, 1)
        layout.addLayout(controls_row)

        # Results area — text LEFT, waveforms RIGHT
        res_label = QLabel(self.translator.get('label_results'))
        res_label.setStyleSheet(
            "font-weight: 700; color: #1a3d28; font-size: 12px;"
            " letter-spacing: 0.4px; padding-left: 2px; padding-top: 4px;"
        )
        layout.addWidget(res_label)

        results_row = QHBoxLayout()
        results_row.setSpacing(12)

        # Left: text output
        self.compat_output = QTextEdit()
        self.compat_output.setReadOnly(True)
        self.compat_output.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.78);
                border: 1px solid rgba(255, 255, 255, 0.70);
                border-top: 1px solid rgba(255, 255, 255, 0.92);
                border-radius: 12px;
                padding: 14px;
                font-size: 11px;
                font-family: 'Courier New', monospace;
            }
        """)
        self.compat_output.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        results_row.addWidget(self.compat_output, 2)

        # Right: waveforms stacked vertically
        waveform_col = QVBoxLayout()
        waveform_col.setSpacing(8)
        self.compat_waveform1 = WaveformWidget(label="Track 1", color="#1DB954")
        self.compat_waveform2 = WaveformWidget(label="Track 2", color="#3B82F6")
        waveform_col.addWidget(self.compat_waveform1, 1)
        waveform_col.addWidget(self.compat_waveform2, 1)
        results_row.addLayout(waveform_col, 3)

        layout.addLayout(results_row, 1)

        widget.setLayout(layout)
        return widget
    
    def create_tips_tab(self):
        """Cria aba de Dicas de DJ"""
        widget = TropicalBackground()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title = QLabel(self.translator.get('tips_title'))
        title_font = QFont("Segoe UI", 18, QFont.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #1DB954; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel(self.translator.get('tips_subtitle_desc'))
        subtitle_font = QFont("Segoe UI", 11)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666; margin-bottom: 20px;")
        layout.addWidget(subtitle)
        
        # Separator
        sep_line = QFrame()
        sep_line.setFrameShape(QFrame.HLine)
        sep_line.setStyleSheet("background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:0, stop:0 #1a4d2e, stop:0.5 #ff9500, stop:1 #c1440e); height: 2px; border: none; margin: 10px 0px;")
        layout.addWidget(sep_line)
        layout.addSpacing(10)
        
        # Tip Display Area — glass card, expands to fill space
        tip_frame = QFrame()
        tip_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.48);
                border: 1px solid rgba(255, 255, 255, 0.72);
                border-top: 2px solid rgba(232, 216, 65, 0.70);
                border-radius: 14px;
                padding: 20px;
            }
        """)
        tip_layout = QVBoxLayout()
        tip_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tip Label (for icon and text)
        self.tip_label = QLabel()
        self.tip_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.tip_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        self.tip_label.setStyleSheet("color: #1a4d2e; line-height: 1.6;")
        self.tip_label.setWordWrap(True)
        self.tip_label.setMinimumHeight(120)
        tip_layout.addWidget(self.tip_label)
        
        tip_frame.setLayout(tip_layout)
        layout.addWidget(tip_frame, 1)
        
        widget.setLayout(layout)
        
        # Load the first tip when tab is created
        self.show_next_tip()
        
        return widget
    
    def show_next_tip(self):
        """Display the next random tip"""
        tip_text = self.tips_manager.get_random_tip()
        self.tip_label.setText(tip_text)
    
    def create_camelot_wheel_tab(self):
        """Cria aba dedicada à Roda Camelot - Nova Tab"""
        widget = TropicalBackground()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        
        # Get language-specific title
        lang = self.translator.get_current_language()
        
        if lang == 'PT':
            wheel_title = "🎡 RODA CAMELOT - Referência de Harmonia"
            wheel_desc = "A Roda Camelot mostra as 24 tonalidades musicais (12 menores + 12 maiores) organizadas em um círculo. Tonalidades próximas na roda harmonizam naturalmente."
            key_info = "🔑 LEITURA DA RODA:\n• NÚMEROS: 1-12 (como um relógio representam 12 tons)\n• A = Tonalidade menor (som mais escuro, triste)\n• B = Tonalidade maior (som mais brilhante, alegre)\n\nExemplo: 8A = Sol# menor  |  3B = Reb maior"
        elif lang == 'ES':
            wheel_title = "🎡 RUEDA CAMELOT - Referencia de Armonía"
            wheel_desc = "La Rueda Camelot muestra las 24 tonalidades musicales (12 menores + 12 mayores) organizadas en un círculo. Las tonalidades cercanas en la rueda armonizan naturalmente."
            key_info = "🔑 LECTURA DE LA RUEDA:\n• NÚMEROS: 1-12 (como un reloj representan 12 tonos)\n• A = Tonalidad menor (sonido más oscuro, triste)\n• B = Tonalidad mayor (sonido más brillante, alegre)\n\nEjemplo: 8A = Sol# menor  |  3B = Reb mayor"
        else:  # ENG (default)
            wheel_title = "🎡 CAMELOT WHEEL - Harmony Reference"
            wheel_desc = "The Camelot Wheel shows the 24 musical keys (12 minor + 12 major) organized in a circle. Keys close together on the wheel harmonize naturally."
            key_info = "🔑 READING THE WHEEL:\n• NUMBERS: 1-12 (like a clock represent 12 pitches)\n• A = Minor key (darker, sadder sound)\n• B = Major key (brighter, happier sound)\n\nExample: 8A = G♯ minor  |  3B = D♭ major"
        
        # ===== WHEEL IMAGE SECTION =====
        wheel_section = QFrame()
        if self._dark:
            wheel_section.setStyleSheet("""
                QFrame {
                    background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1,
                        stop:0 #2a2a2a,
                        stop:1 #1f1f1f
                    );
                    border: 3px solid #e8d841;
                    border-radius: 12px;
                    padding: 24px;
                }
            """)
        else:
            wheel_section.setStyleSheet("""
                QFrame {
                    background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1,
                        stop:0 #f9fafb,
                        stop:1 #f3f4f6
                    );
                    border: 3px solid #e8d841;
                    border-radius: 12px;
                    padding: 24px;
                }
            """)
        wheel_layout = QVBoxLayout()
        wheel_layout.setSpacing(16)
        wheel_layout.setContentsMargins(0, 0, 0, 0)
        
        # Wheel Title
        wheel_title_label = QLabel(wheel_title)
        wheel_title_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        wheel_title_label.setAlignment(Qt.AlignCenter)
        if self._dark:
            wheel_title_label.setStyleSheet("color: #4ADE80; letter-spacing: 0.5px; margin-bottom: 10px;")
        else:
            wheel_title_label.setStyleSheet("color: #1DB954; letter-spacing: 0.5px; margin-bottom: 10px;")
        wheel_layout.addWidget(wheel_title_label)
        
        # Try to load wheel image
        wheel_image_added = False
        assets_dir = get_assets_dir()
        
        # Try to load the Camelot wheel image
        for image_name in ["camelot_wheel.png", "camelot_wheel.jpg", "camelot_wheel.svg"]:
            image_path = assets_dir / image_name
            if image_path.exists():
                try:
                    if image_name.endswith(".svg"):
                        wheel_svg = QSvgWidget(str(image_path))
                        wheel_svg.setMaximumHeight(550)
                        wheel_layout.addWidget(wheel_svg, alignment=Qt.AlignCenter)
                    else:
                        wheel_pixmap = QPixmap(str(image_path))
                        if not wheel_pixmap.isNull():
                            wheel_pixmap = wheel_pixmap.scaledToHeight(550, Qt.SmoothTransformation)
                            wheel_img_label = QLabel()
                            wheel_img_label.setPixmap(wheel_pixmap)
                            wheel_img_label.setAlignment(Qt.AlignCenter)
                            wheel_layout.addWidget(wheel_img_label)
                    wheel_image_added = True
                    break
                except:
                    pass
        
        if not wheel_image_added:
            # Display text-based Camelot wheel representation
            wheel_text = self._get_camelot_wheel_text()
            wheel_display = QLabel(wheel_text)
            wheel_display.setFont(QFont("Courier New", 10))
            wheel_display.setAlignment(Qt.AlignCenter)
            if self._dark:
                wheel_display.setStyleSheet("color: #C0C0C0; background: #1a1a1a; padding: 20px; border-radius: 8px; line-height: 1.6;")
            else:
                wheel_display.setStyleSheet("color: #333; background: white; padding: 20px; border-radius: 8px; line-height: 1.6;")
            wheel_layout.addWidget(wheel_display)
        
        # Description
        wheel_layout.addSpacing(12)
        desc_label = QLabel(wheel_desc)
        desc_label.setFont(QFont("Segoe UI", 12))
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        if self._dark:
            desc_label.setStyleSheet("color: #C0C0C0; max-width: 600px; line-height: 1.6;")
        else:
            desc_label.setStyleSheet("color: #000000; max-width: 600px; line-height: 1.6;")
        wheel_layout.addWidget(desc_label)
        
        wheel_section.setLayout(wheel_layout)
        content_layout.addWidget(wheel_section)
        
        # ===== KEY INFO SECTION =====
        info_section = QFrame()
        if self._dark:
            info_section.setStyleSheet("""
                QFrame {
                    background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1,
                        stop:0 #2a2a2a,
                        stop:1 #1f1f1f
                    );
                    border: 2px solid #4ADE80;
                    border-radius: 12px;
                    padding: 20px;
                }
            """)
        else:
            info_section.setStyleSheet("""
                QFrame {
                    background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1,
                        stop:0 #f3f4f6,
                        stop:1 #f9fafb
                    );
                    border: 2px solid #1DB954;
                    border-radius: 12px;
                    padding: 20px;
                }
            """)
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        key_info_label = QLabel(key_info)
        key_info_label.setFont(QFont("Segoe UI", 11))
        key_info_label.setAlignment(Qt.AlignCenter)
        key_info_label.setWordWrap(True)
        if self._dark:
            key_info_label.setStyleSheet("color: #E0E0E0; line-height: 1.8;")
        else:
            key_info_label.setStyleSheet("color: #000000; line-height: 1.8;")
        info_layout.addWidget(key_info_label)
        
        info_section.setLayout(info_layout)
        content_layout.addWidget(info_section)
        
        # ===== MIXING TIPS SECTION =====
        tips_section = QFrame()
        if self._dark:
            tips_section.setStyleSheet("""
                QFrame {
                    background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1,
                        stop:0 #2a2a2a,
                        stop:1 #1f1f1f
                    );
                    border: 2px solid #d4a574;
                    border-radius: 12px;
                    padding: 20px;
                }
            """)
        else:
            tips_section.setStyleSheet("""
                QFrame {
                    background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1,
                        stop:0 #fff9e6,
                        stop:1 #fff3cc
                    );
                    border: 2px solid #f4d03f;
                    border-radius: 12px;
                    padding: 20px;
                }
            """)
        tips_layout = QVBoxLayout()
        tips_layout.setContentsMargins(0, 0, 0, 0)
        
        if lang == 'PT':
            tips_title = "💡 Dicas de Mistura Harmônica"
            tips_text = (
                "✓ Mesma tonalidade: Mix perfeito (ex: 8A → 8A)\n"
                "✓ ±1 semitom: Mudança de energia (ex: 8A → 8B ou 7A)\n"
                "✓ ±5 semitons: Relação harmônica (ex: 8A → 3A)\n"
                "✓ Evitar: Tons distantes no círculo (quebra harmonia)\n"
                "✓ Dica: Use a Roda Camelot para harmonia suave!"
            )
        elif lang == 'ES':
            tips_title = "💡 Consejos de Mezcla Armónica"
            tips_text = (
                "✓ Misma tonalidad: Mix perfecto (ej: 8A → 8A)\n"
                "✓ ±1 semitono: Cambio de energía (ej: 8A → 8B o 7A)\n"
                "✓ ±5 semitonos: Relación armónica (ej: 8A → 3A)\n"
                "✓ Evitar: Tonos distantes en el círculo (rompe armonía)\n"
                "✓ Consejo: ¡Usa la Rueda Camelot para mezcla suave!"
            )
        else:  # ENG
            tips_title = "💡 Harmonic Mixing Tips"
            tips_text = (
                "✓ Same key: Perfect mix (e.g., 8A → 8A)\n"
                "✓ ±1 semitone: Energy shift (e.g., 8A → 8B or 7A)\n"
                "✓ ±5 semitones: Harmonic relation (e.g., 8A → 3A)\n"
                "✓ Avoid: Distant keys on circle (breaks harmony)\n"
                "✓ Pro Tip: Use Camelot Wheel for smooth mixing!"
            )
        
        tips_title_label = QLabel(tips_title)
        tips_title_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        if self._dark:
            tips_title_label.setStyleSheet("color: #FFD700; margin-bottom: 10px;")
        else:
            tips_title_label.setStyleSheet("color: #000000; margin-bottom: 10px;")
        tips_layout.addWidget(tips_title_label)
        
        tips_text_label = QLabel(tips_text)
        tips_text_label.setFont(QFont("Segoe UI", 11))
        tips_text_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        tips_text_label.setWordWrap(True)
        if self._dark:
            tips_text_label.setStyleSheet("color: #E0E0E0; line-height: 1.8;")
        else:
            tips_text_label.setStyleSheet("color: #000000; line-height: 1.8;")
        tips_layout.addWidget(tips_text_label)
        
        tips_section.setLayout(tips_layout)
        content_layout.addWidget(tips_section)
        
        content_layout.addStretch()
        scroll_content.setLayout(content_layout)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        widget.setLayout(main_layout)
        return widget
    
    def _camel_pixmap(self, dark: bool) -> QPixmap:
        """Render the camel silhouette at 220×188 with day/night colouring."""
        fill = b'#c8a820' if dark else b'#1a1a1a'
        svg = _CAMEL_SVG_TMPL.replace(b'FILLCOLOR', fill)
        renderer = QSvgRenderer(svg)
        pix = QPixmap(220, 188)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        renderer.render(p)
        p.end()
        return pix

    def create_about_tab(self):
        """Cria aba Sobre — text + camel silhouette side-by-side."""
        widget = TropicalBackground()
        layout = QHBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # ---- LEFT: about text ----
        app_info = QTextEdit()
        app_info.setReadOnly(True)
        self._about_info = app_info
        app_info.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.78);
                border: 1px solid rgba(255, 255, 255, 0.70);
                border-top: 2px solid rgba(29, 185, 84, 0.55);
                border-radius: 12px;
                padding: 20px;
                font-size: 12px;
                line-height: 1.6;
                color: #222222;
            }
        """)

        lang = self.translator.get_current_language()
        if lang == 'PT':
            about_content = """
CAMEL-HOT - Analisador de Música Harmônica v2.0

----------------------------------------------

O que é?
--------
Um aplicativo que analisa sua música e a organiza por tom musical,
facilitando a mixagem harmônica profissional como os DJs fazem.

IMPORTANTE - APLICATIVO 100% OFFLINE
-------------------------------------
Este aplicativo é totalmente offline e não se conecta a nenhum
serviço externo, software de DJ ou streaming. É uma ferramenta
local de análise e organização de sua biblioteca pessoal.

Recursos Principais:
--------------------
✓ Detectar tom musical, BPM e duração das músicas
✓ Converter para notação Camelot (padrão DJ)
✓ Organizar sua biblioteca por tom musical
✓ Criar playlists de mistura harmônica
✓ Verificar compatibilidade de tom para mixagem suave

Formatos de Áudio Suportados:
-----------------------------
MP3 • WAV • FLAC • OGG • M4A • AIFF

Feito para DJs e amantes de música!
            """
        elif lang == 'ES':
            about_content = """
CAMEL-HOT - Analizador de Música Armónica v2.0

=======================================

¿Qué es?
------------
Una aplicación que analiza tu música y la organiza por tonalidad musical,
facilitando la mezcla armónica profesional como lo hacen los DJs.

🔒 IMPORTANTE — APLICACIÓN 100% OFFLINE
--------------------------------------
Esta aplicación es completamente offline y no se conecta a ningún
servicio externo, software de DJ o streaming. Es una herramienta
local de análisis y organización de tu biblioteca personal.

Características Principales:
------------------------
✓ Detectar tonalidad, BPM y duración de canciones
✓ Convertir a notación Camelot (estándar DJ)
✓ Organizar tu biblioteca por tonalidad
✓ Crear listas de mezcla armónica
✓ Verificar compatibilidad de tonalidad para mezclas suaves

Formatos de Audio Compatibles:
------------------------------
MP3 • WAV • FLAC • OGG • M4A • AIFF

¡Hecho para DJs y amantes de la música!
            """
        else:
            about_content = """
CAMEL-HOT - Harmonic Music Analyzer v2.0

═══════════════════════════════════════════════════════════

What is this?
------------
An application that analyzes your music and organizes it by musical key,
facilitating professional harmonic mixing like DJs do.

🔒 IMPORTANT — 100% OFFLINE APPLICATION

This application is completely offline and does not connect to any
external services, DJ software, or streaming services. It is a local
tool for analyzing and organizing your personal music library.

Key Features:

✓ Detect musical key, BPM and duration of songs
✓ Convert to Camelot notation (DJ standard)
✓ Organize your library by musical key
✓ Create harmonic mixing playlists
✓ Check key compatibility for smooth mixing

Supported Audio Formats:

MP3 • WAV • FLAC • OGG • M4A • AIFF

Made for DJs and music lovers!
            """

        app_info.setText(about_content)
        layout.addWidget(app_info, 7)

        # ---- RIGHT: camel silhouette ----
        self._camel_label = QLabel()
        self._camel_label.setPixmap(self._camel_pixmap(self._dark))
        self._camel_label.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        self._camel_label.setStyleSheet("background: transparent; border: none;")
        self._camel_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self._camel_label.setMinimumWidth(180)
        layout.addWidget(self._camel_label, 3)

        widget.setLayout(layout)
        return widget

    def _get_camelot_wheel_text(self):
        """Returns a text-based Camelot Wheel reference when no image is available."""
        return (
            "CAMELOT WHEEL \u2014 Key Reference\n"
            "\u2550" * 54 + "\n"
            "Position  Minor (A)           Major (B)\n"
            "\u2500" * 54 + "\n"
            "   1      A minor             C major\n"
            "   2      E minor             G major\n"
            "   3      B minor             D major\n"
            "   4      F\u266f minor             A major\n"
            "   5      C\u266f / D\u266d minor       E major\n"
            "   6      G\u266f / A\u266d minor       B major\n"
            "   7      E\u266d minor             F\u266f / G\u266d major\n"
            "   8      B\u266d minor             D\u266d major\n"
            "   9      F minor             A\u266d major\n"
            "  10      C minor             E\u266d major\n"
            "  11      G minor             B\u266d major\n"
            "  12      D minor             F major\n"
            "\u2550" * 54 + "\n"
            "Compatible keys: same number \u00b11  |  same number A\u2194B"
        )

    def browse_analyze_file(self):
        """Abre diálogo para selecionar arquivo"""
        file_dialog = QFileDialog()
        file_dialog.setStyleSheet(self.get_file_dialog_stylesheet())
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Selecione um arquivo de áudio",
            "",
            "Arquivos de Áudio (*.mp3 *.wav *.flac *.ogg *.m4a *.aiff);;Todos os arquivos (*)"
        )
        if file_path:
            self.selected_file = file_path
            self.analyze_file_input.setText(file_path)
    
    def browse_org_input(self):
        """Seleciona pasta de entrada para organizar"""
        folder_dialog = QFileDialog()
        folder_dialog.setStyleSheet(self.get_file_dialog_stylesheet())
        folder = folder_dialog.getExistingDirectory(self, "Selecione a pasta com músicas")
        if folder:
            self.selected_input_folder = folder
            self.org_input.setText(folder)
    
    def browse_org_output(self):
        """Seleciona pasta de saída para organizar"""
        folder_dialog = QFileDialog()
        folder_dialog.setStyleSheet(self.get_file_dialog_stylesheet())
        folder = folder_dialog.getExistingDirectory(self, "Selecione a pasta de saída")
        if folder:
            self.selected_output_folder = folder
            self.org_output.setText(folder)
    
    def browse_pl_input(self):
        """Seleciona pasta para criar playlist"""
        folder_dialog = QFileDialog()
        folder_dialog.setStyleSheet(self.get_file_dialog_stylesheet())
        folder = folder_dialog.getExistingDirectory(self, "Selecione a pasta com músicas")
        if folder:
            self.pl_input.setText(folder)
    
    def browse_compat_file1(self):
        """Abre diálogo para selecionar primeiro arquivo"""
        file_dialog = QFileDialog()
        file_dialog.setStyleSheet(self.get_file_dialog_stylesheet())
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Selecione o primeiro arquivo de áudio",
            "",
            "Arquivos de Áudio (*.mp3 *.wav *.flac *.ogg *.m4a *.aiff);;Todos os arquivos (*)"
        )
        if file_path:
            self.compat_file1_path = file_path
            self.compat_file1.setText(file_path)
    
    def browse_compat_file2(self):
        """Abre diálogo para selecionar segundo arquivo"""
        file_dialog = QFileDialog()
        file_dialog.setStyleSheet(self.get_file_dialog_stylesheet())
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Selecione o segundo arquivo de áudio",
            "",
            "Arquivos de Áudio (*.mp3 *.wav *.flac *.ogg *.m4a *.aiff);;Todos os arquivos (*)"
        )
        if file_path:
            self.compat_file2_path = file_path
            self.compat_file2.setText(file_path)
    
    def handle_transition_comparison(self):
        """Compara compatibilidade de transição entre dois arquivos"""
        if not hasattr(self, 'compat_file1_path') or not hasattr(self, 'compat_file2_path'):
            QMessageBox.warning(self, "Aviso", "Selecione ambos os arquivos!")
            return
        if not self.compat_file1_path or not self.compat_file2_path:
            QMessageBox.warning(self, "Aviso", "Selecione ambos os arquivos!")
            return

        # Stop any previously running transition worker
        existing = getattr(self, 'transition_worker', None)
        if existing is not None and existing.isRunning():
            existing.quit()
            existing.wait(2000)

        dark = getattr(self, '_dark', False)
        self._progress_dialog = RealTimeProgressDialog(
            self, title="⇄ Transition Analysis", dark=dark, total_files=2
        )
        self.transition_worker = TransitionWorker(
            self.compat_file1_path, self.compat_file2_path
        )
        self.transition_worker.progress.connect(self._progress_dialog.update_progress)
        self.transition_worker.file_tick.connect(self._progress_dialog.update_file)
        self.transition_worker.result.connect(self._on_transition_result)
        self.transition_worker.error.connect(self._on_transition_error)
        self.transition_worker.finished.connect(self._on_transition_finished)
        self._progress_dialog.show()
        self.transition_worker.start()

    def _on_transition_result(self, data):
        """Display transition comparison result."""
        track1 = data['track1']
        track2 = data['track2']
        transition = data['transition']
        output = "🎛️ TRANSITION COMPARISON\n"
        output += "═" * 70 + "\n\n"
        output += f"Track 1: {os.path.basename(self.compat_file1_path)}\n"
        output += f"  🎵 Key: {track1.get('key', 'Unknown')} ({track1.get('camelot', 'Unknown')})\n"
        output += f"  ⏱️  BPM: {track1.get('bpm', 'Unknown')}\n"
        output += f"  😊 Mood: {track1.get('mood', {}).get('primary_mood', 'Unknown')}\n"
        output += f"  🥁 Groove: {track1.get('groove', {}).get('type', 'Unknown')}\n"
        output += f"  ⚡ Energy: {track1.get('energy', {}).get('level', 'Unknown')}\n\n"
        output += f"Track 2: {os.path.basename(self.compat_file2_path)}\n"
        output += f"  🎵 Key: {track2.get('key', 'Unknown')} ({track2.get('camelot', 'Unknown')})\n"
        output += f"  ⏱️  BPM: {track2.get('bpm', 'Unknown')}\n"
        output += f"  😊 Mood: {track2.get('mood', {}).get('primary_mood', 'Unknown')}\n"
        output += f"  🥁 Groove: {track2.get('groove', {}).get('type', 'Unknown')}\n"
        output += f"  ⚡ Energy: {track2.get('energy', {}).get('level', 'Unknown')}\n\n"
        output += "┌─ TRANSITION COMPATIBILITY SCORES\n"
        output += f"│  Overall:   {transition.get('overall_score', 0):.2f}/1.0  {transition.get('recommendation', '')}\n"
        output += f"│  Harmonic:  {transition.get('harmonic_score', 0):.2f}  (Camelot wheel)\n"
        output += f"│  Energy:    {transition.get('energy_score', 0):.2f}  (Spectral shift)\n"
        output += f"│  Groove:    {transition.get('groove_score', 0):.2f}  (Rhythm match)\n"
        output += f"│  Mood:      {transition.get('mood_score', 0):.2f}  (Emotional fit)\n"
        output += f"│  BPM:       {transition.get('bpm_score', 0):.2f}  (Tempo match)\n"
        output += "└─\n\n"
        output += "💡 NOTES:\n"
        for note in transition.get('notes', []):
            output += f"   {note}\n"
        output += "\n" + "═" * 70 + "\n"
        self.compat_output.setText(output)
        if hasattr(self, '_progress_dialog') and self._progress_dialog:
            self._progress_dialog.set_complete("Analysis complete!")

        # Load waveforms for both tracks
        self._load_compat_waveforms()

    def _load_compat_waveforms(self):
        """Start background waveform loading for both tracks."""
        f1 = getattr(self, 'compat_file1_path', None)
        f2 = getattr(self, 'compat_file2_path', None)
        if f1:
            self.compat_waveform1.set_label(f"Track 1: {os.path.basename(f1)}")
            self._wf_worker1 = WaveformWorker(f1)
            self._wf_worker1.waveform_ready.connect(self.compat_waveform1.set_data)
            self._wf_worker1.start()
        if f2:
            self.compat_waveform2.set_label(f"Track 2: {os.path.basename(f2)}")
            self._wf_worker2 = WaveformWorker(f2)
            self._wf_worker2.waveform_ready.connect(self.compat_waveform2.set_data)
            self._wf_worker2.start()

    def _on_transition_error(self, error_msg):
        if hasattr(self, '_progress_dialog') and self._progress_dialog:
            self._progress_dialog.set_error(error_msg)
        else:
            QMessageBox.critical(self, "Erro", f"Erro ao comparar:\n{error_msg}")

    def _on_transition_finished(self):
        pass
    
    def handle_analyze(self):
        """Analisa um arquivo com progresso"""
        if not self.selected_file:
            QMessageBox.warning(self, "Aviso", "Selecione um arquivo!")
            return

        # Stop any previously running analysis worker
        if self.analysis_worker is not None and self.analysis_worker.isRunning():
            self.analysis_worker.quit()
            self.analysis_worker.wait(2000)
        
        # Create and show real-time progress dialog
        dark = getattr(self, '_dark', False)
        self.progress_dialog = RealTimeProgressDialog(
            self, title="🎵 Track Analysis", dark=dark, total_files=1
        )
        
        # Create worker thread
        self.analysis_worker = AnalysisWorker(self.selected_file)
        self.analysis_worker.progress.connect(self.progress_dialog.update_progress)
        self.analysis_worker.file_tick.connect(self.progress_dialog.update_file)
        self.analysis_worker.result.connect(self._on_analysis_result)
        self.analysis_worker.error.connect(self._on_analysis_error)
        self.analysis_worker.finished.connect(self._on_analysis_finished)
        
        self.progress_dialog.show()
        self.analysis_worker.start()
    
    def _on_analysis_result(self, result):
        """Process analysis result"""
        try:
            # Build confidence bar visualization
            confidence = result.get('confidence', 0.0)
            confidence_pct = int(confidence * 100)
            bar_length = 30
            filled = int((confidence_pct / 100) * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            
            # Build output with all features
            output = f"🔄 Análise #{self.analyze_output.toPlainText().count('Arquivo:') + 1}\n"
            output += "═" * 70 + "\n\n"
            
            # Basic Info
            output += "📋 INFORMAÇÃO BÁSICA\n"
            output += f"  📀 Arquivo:     {os.path.basename(self.selected_file)}\n"
            output += f"  ⏰ Duração:     {result.get('duration', 'Desconhecida')} segundos\n"
            output += f"  🎵 Tonalidade:  {result.get('key', 'Desconhecido')}\n"
            output += f"  🎼 Camelot:     {result.get('camelot', 'Desconhecido')}\n"
            output += f"  ⏱️  BPM:         {result.get('bpm', 'Desconhecido')}\n"
            output += "\n"
            
            # Key Confidence
            output += f"📊 Confiança da Análise:\n"
            output += f"   [{bar}] {confidence_pct}%\n"
            output += "\n"
            
            # Energy Level
            energy = result.get('energy')
            if energy:
                output += "⚡ NÍVEL DE ENERGIA\n"
                output += f"  Nível:        {energy.get('level', 'Desconhecido')}\n"
                output += f"  Brilho:       {energy.get('brightness', 'Desconhecido')} ({energy.get('brightness_score', 0):.2f})\n"
                output += f"  Densidade:    {energy.get('density', 'Desconhecido')} ({energy.get('richness_score', 0):.2f})\n"
                output += f"  Dinâmica:     {energy.get('energy_curve', 'Desconhecido')}\n"
                output += f"  Score Geral:  {energy.get('overall_score', 0):.2f}/1.0\n"
                output += "\n"
            
            # Groove
            groove = result.get('groove')
            if groove:
                output += "🥁 GROOVE & RITMO\n"
                output += f"  Tipo:         {groove.get('type', 'Desconhecido')}\n"
                output += f"  Kick:         {groove.get('kick_presence', 0):.2f} (presente), {groove.get('kick_regularity', 0):.2f} (regular)\n"
                output += f"  Percussão:    {groove.get('percussion_density', 0):.2f}\n"
                output += f"  Swing:        {groove.get('swing', 0):.2f}\n"
                output += "\n"
            
            # Mood
            mood = result.get('mood')
            if mood:
                output += "😊 HUMOR & EMOÇÃO\n"
                output += f"  Humor Principal: {mood.get('primary_mood', 'Desconhecido')}\n"
                output += f"  Tonalidade:      {'Maior' if mood.get('is_major') else 'Menor'}\n"
                output += f"  Agressividade:   {mood.get('aggressiveness', 0):.2f}\n"
                output += f"  Brilho:          {mood.get('brightness', 0):.2f}\n"
                output += f"  Tensão Harmônica: {mood.get('tension', 0):.2f}\n"
                output += "\n"
                
                # All mood scores
                all_moods = mood.get('all_moods', {})
                if all_moods:
                    output += "  Scores de Humor:\n"
                    for mood_name, score in sorted(all_moods.items(), key=lambda x: x[1], reverse=True):
                        bar_len = 15
                        filled = int(score * bar_len)
                        mood_bar = "█" * filled + "░" * (bar_len - filled)
                        output += f"    {mood_name:15} {mood_bar} {score:.1%}\n"
                    output += "\n"
            
            output += "✅ Análise concluída com sucesso!\n"
            output += "═" * 70 + "\n\n"
            
            # Store result in list
            self.analysis_results.append({
                'output': output,
                'result': result
            })
            
            # Display all results side-by-side in pairs
            self.display_results_side_by_side()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao processar resultado:\n{str(e)}")
    
    def _on_analysis_error(self, error_msg):
        """Handle analysis error"""
        if self.progress_dialog:
            self.progress_dialog.set_error(error_msg)
        else:
            QMessageBox.critical(self, "Erro", f"Erro ao analisar:\n{error_msg}")
    
    def _on_analysis_finished(self):
        """Analysis finished"""
        if self.progress_dialog:
            self.progress_dialog.set_complete("Analysis complete!")
            self.progress_dialog = None
    
    def display_results_side_by_side(self):
        """Display analysis results side-by-side with far-left and far-right positioning"""
        if not self.analysis_results:
            return
        
        # Split results into lines for each analysis
        all_lines = []
        for result_data in self.analysis_results:
            lines = result_data['output'].strip().split('\n')
            all_lines.append(lines)
        
        # Build output - push analyses to opposite ends
        display_output = ""
        
        # Calculate available width based on monospace font at typical text box size
        # Approximate usable width for side-by-side display
        left_max_width = 85  # Left analysis max width - more generous for output content
        right_start_column = 140  # Column where right analysis begins (pushed far right)
        
        # Process results in pairs
        for i in range(0, len(all_lines), 2):
            left_lines = all_lines[i] if i < len(all_lines) else []
            right_lines = all_lines[i + 1] if i + 1 < len(all_lines) else []
            
            # Determine max lines for this row
            max_lines = max(len(left_lines), len(right_lines))
            
            # Build side-by-side layout with dynamic spacing
            for line_idx in range(max_lines):
                left_line = left_lines[line_idx] if line_idx < len(left_lines) else ""
                right_line = right_lines[line_idx] if line_idx < len(right_lines) else ""
                
                # Truncate left line if too long
                if len(left_line) > left_max_width:
                    left_line = left_line[:left_max_width - 3] + "..."
                
                # Build the line with dynamic spacing
                if right_line:
                    # Calculate padding needed to push right line to far right
                    current_length = len(left_line)
                    padding_needed = right_start_column - current_length
                    if padding_needed < 1:
                        padding_needed = 3
                    
                    # Combine with dynamic padding
                    line_output = left_line + " " * padding_needed + right_line
                    display_output += line_output + "\n"
                else:
                    # Only left content
                    display_output += left_line + "\n"
            
            # Add separator between pairs
            display_output += "\n" + "=" * 180 + "\n\n"
        
        # Set the display
        self.analyze_output.setText(display_output)
        
        # Scroll to bottom
        self.analyze_output.verticalScrollBar().setValue(
            self.analyze_output.verticalScrollBar().maximum()
        )
    
    def handle_organize(self):
        """Organiza biblioteca com progresso"""
        if not self.selected_input_folder or not self.selected_output_folder:
            QMessageBox.warning(self, "Aviso", "Selecione ambas as pastas!")
            return

        # Stop any previously running organization worker
        if self.organization_worker is not None and self.organization_worker.isRunning():
            self.organization_worker.cancel()
            self.organization_worker.wait(2000)

        dark = getattr(self, '_dark', False)

        # Ask user for the parent folder name
        next_num = get_next_org_number(self.selected_output_folder)
        default_name = f"CH_Org{next_num}"
        dlg = FolderNamingDialog(
            parent=self,
            default_name=default_name,
            target_dir=self.selected_output_folder,
            dark=dark,
        )
        if dlg.exec_() != QDialog.Accepted:
            return
        folder_name = dlg.get_folder_name()

        # Estimate file count for the progress dialog
        try:
            audio_files = find_audio_files(self.selected_input_folder)
            total = len(audio_files)
        except Exception:
            total = 0

        self._progress_dialog = RealTimeProgressDialog(
            self, title="⊞ Organizing Library", dark=dark, total_files=total
        )
        self.organization_worker = OrganizationWorker(
            self.selected_input_folder,
            self.selected_output_folder,
            self.move_files.isChecked(),
            parent_folder_name=folder_name,
        )
        self.organization_worker.progress.connect(self._progress_dialog.update_progress)
        self.organization_worker.file_tick.connect(self._progress_dialog.update_file)
        self.organization_worker.result.connect(self._on_organize_result)
        self.organization_worker.error.connect(self._on_organize_error)
        self.organization_worker.finished.connect(self._on_organize_finished)
        self._progress_dialog.cancelled.connect(self.organization_worker.cancel)
        self._progress_dialog.show()
        self.organization_worker.start()
    
    def _on_organize_progress(self, value, message):
        """Handled via direct signal connection to RealTimeProgressDialog."""
        pass
    
    def _on_organize_result(self, result):
        """Process organization result"""
        try:
            total = result.get('total_files', 0)
            organized = result.get('organized_count', 0)
            out_dir = self.selected_output_folder
            output = f"✅ Total files: {total}\n"
            output += f"✅ Organized: {organized}\n"
            output += f"\n📁 Output folder:\n{out_dir}\n\n"
            if result.get('by_key'):
                output += "Distribution by key:\n"
                for key in sorted(result['by_key'].keys()):
                    count = len(result['by_key'][key])
                    output += f"  • {key}: {count} tracks\n"
            output += "\n✅ Organization complete!"
            self.org_output_text.setText(output)
            if hasattr(self, '_progress_dialog') and self._progress_dialog:
                self._progress_dialog.set_complete(
                    f"Done — {organized} files organized"
                )
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao processar resultado:\n{str(e)}")
    
    def _on_organize_error(self, error_msg):
        """Handle organization error"""
        if hasattr(self, '_progress_dialog') and self._progress_dialog:
            self._progress_dialog.set_error(error_msg)
        else:
            QMessageBox.critical(self, "Erro", f"Erro ao organizar:\n{error_msg}")
    
    def _on_organize_finished(self):
        """Organization finished — dialog stays open until user closes it."""
        pass
    
    def handle_playlist(self):
        """Cria playlist baseado no modo selecionado com progresso"""
        if not self.pl_input.text():
            QMessageBox.warning(self, "Aviso", "Selecione uma pasta!")
            return

        # Stop any previously running playlist worker
        if self.playlist_worker is not None and self.playlist_worker.isRunning():
            self.playlist_worker.cancel()
            self.playlist_worker.wait(2000)
        
        output_file = self.pl_output.text().strip()
        if not output_file:
            output_file = "my_playlist.m3u"
        if not output_file.endswith('.m3u'):
            output_file += '.m3u'
        
        mode = self.pl_mode_group.checkedId()
        
        dark = getattr(self, '_dark', False)
        self._progress_dialog = RealTimeProgressDialog(
            self, title="♫ Building Playlist", dark=dark
        )
        # Read energy/groove filters
        energy_sel = self.pl_energy.currentText()
        energy_filter = None if energy_sel == "Any" else energy_sel
        groove_sel = self.pl_groove.currentText()
        groove_filter = None if groove_sel == "Any" else groove_sel

        # Prepare arguments based on mode
        if mode == 0:  # Simple Harmonic
            key = self.pl_key.currentText()
            if key == "Any":
                key = None
            bpm_min = self.pl_bpm_min.value()
            bpm_max = self.pl_bpm_max.value()
            limit = self.pl_limit.value()
            bpm_range = None
            if (bpm_min > 0) or (bpm_max < 300):
                bpm_range = (bpm_min, bpm_max)
            
            self.playlist_worker = PlaylistWorker(
                create_harmonic_playlist,
                input_directory=self.pl_input.text(),
                output_file=output_file,
                target_key=key,
                bpm_range=bpm_range,
                max_songs=limit,
                energy_filter=energy_filter,
                groove_filter=groove_filter
            )
            self._playlist_mode = 0
            self._playlist_output_file = output_file
            self._playlist_key = key
            
        elif mode == 1:  # Harmonic Sequence
            start_key = self.pl_seq_start.currentText()
            direction = self.pl_direction.currentText()
            seq_length = 8
            max_per_key = 3
            
            self.playlist_worker = PlaylistWorker(
                create_harmonic_sequence_playlist,
                input_directory=self.pl_input.text(),
                output_file=output_file,
                start_key=start_key,
                sequence_length=seq_length,
                direction=direction,
                max_songs_per_key=max_per_key
            )
            self._playlist_mode = 1
            self._playlist_output_file = output_file
            self._playlist_start_key = start_key
            self._playlist_direction = direction
            
        elif mode == 2:  # Key Transition
            start_key = self.pl_seq_start.currentText()
            target_key = self.pl_target_key.currentText()
            limit = self.pl_limit.value()
            
            self.playlist_worker = PlaylistWorker(
                create_key_to_key_playlist,
                input_directory=self.pl_input.text(),
                output_file=output_file,
                start_key=start_key,
                target_key=target_key,
                max_songs=limit
            )
            self._playlist_mode = 2
            self._playlist_output_file = output_file
            self._playlist_start_key = start_key
            self._playlist_target_key = target_key
            
        elif mode == 3:  # Camelot Zone
            target_key = self.pl_key.currentText()
            if target_key == "Any":
                target_key = "8A"
            limit = self.pl_limit.value()
            
            self.playlist_worker = PlaylistWorker(
                create_camelot_zone_playlist,
                input_directory=self.pl_input.text(),
                output_file=output_file,
                target_key=target_key,
                zone_size=2,
                max_songs=limit
            )
            self._playlist_mode = 3
            self._playlist_output_file = output_file
            self._playlist_target_key = target_key
        
        # Connect signals and start
        self.playlist_worker.progress.connect(self._progress_dialog.update_progress)
        self.playlist_worker.file_tick.connect(self._progress_dialog.update_file)
        self.playlist_worker.result.connect(self._on_playlist_result)
        self.playlist_worker.error.connect(self._on_playlist_error)
        self.playlist_worker.finished.connect(self._on_playlist_finished)
        self._progress_dialog.cancelled.connect(self.playlist_worker.cancel)
        self._progress_dialog.show()
        self.playlist_worker.start()
    
    def _on_playlist_progress(self, value, message):
        """Handled via direct signal connection to RealTimeProgressDialog."""
        pass
    
    def _on_playlist_result(self, result_dict):
        """Process playlist result"""
        try:
            result = result_dict.get('result', [])
            mode = getattr(self, '_playlist_mode', 0)
            output_file = getattr(self, '_playlist_output_file', '')

            if mode == 0:  # Simple Harmonic
                key = getattr(self, '_playlist_key', None)
                output = f"✅ Simple Harmonic Playlist created!\n"
                output += f"📁 File: {output_file}\n"
                output += f"🎵 Tracks: {len(result)}\n"
                output += f"🎼 Key: {key or 'Any'}\n"
                output += f"\n✅ Ready to play!"

            elif mode == 1:  # Harmonic Sequence
                start_key = getattr(self, '_playlist_start_key', '')
                direction = getattr(self, '_playlist_direction', '')
                output = f"✅ Harmonic Sequence Playlist created!\n"
                output += f"📁 File: {output_file}\n"
                output += f"🎵 Tracks: {len(result)}\n"
                output += f"🎼 Start key: {start_key}  Direction: {direction}\n"
                output += f"\n✅ Harmonic sequence ready!"

            elif mode == 2:  # Key Transition
                start_key = getattr(self, '_playlist_start_key', '')
                target_key = getattr(self, '_playlist_target_key', '')
                output = f"✅ Key Transition Playlist created!\n"
                output += f"📁 File: {output_file}\n"
                output += f"🎵 Tracks: {len(result)}\n"
                output += f"🎼 Transition: {start_key} → {target_key}\n"
                output += f"\n✅ Harmonic transition ready!"

            elif mode == 3:  # Camelot Zone
                target_key = getattr(self, '_playlist_target_key', '')
                output = f"✅ Camelot Zone Playlist created!\n"
                output += f"📁 File: {output_file}\n"
                output += f"🎵 Tracks: {len(result)}\n"
                output += f"🎼 Center key: {target_key}\n"
                output += f"\n✅ All tracks are harmonically compatible!"

            else:
                output = f"✅ Playlist created: {output_file}\n"

            self.pl_output_text.setText(output)
            if hasattr(self, '_progress_dialog') and self._progress_dialog:
                self._progress_dialog.set_complete(
                    f"{len(result)} tracks → {os.path.basename(output_file)}"
                )
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao processar resultado:\n{str(e)}")
    
    def _on_playlist_error(self, error_msg):
        """Handle playlist error"""
        if hasattr(self, '_progress_dialog') and self._progress_dialog:
            self._progress_dialog.set_error(error_msg)
        else:
            QMessageBox.critical(self, "Erro", f"Erro ao criar playlist:\n{error_msg}")
    
    def _on_playlist_finished(self):
        """Playlist creation finished — dialog stays open until user closes it."""
        pass
    
    def _handle_simple_playlist(self, output_file):
        """Cria playlist simples harmônica"""
        key = self.pl_key.currentText()
        if key == "Any":
            key = None
        
        bpm_min = self.pl_bpm_min.value()
        bpm_max = self.pl_bpm_max.value()
        limit = self.pl_limit.value()
        
        bpm_range = None
        if (bpm_min > 0) or (bpm_max < 300):
            bpm_range = (bpm_min, bpm_max)
        
        result = create_harmonic_playlist(
            input_directory=self.pl_input.text(),
            output_file=output_file,
            target_key=key,
            bpm_range=bpm_range,
            max_songs=limit
        )
        
        output = f"✅ Simple Harmonic Playlist criada!\n"
        output += f"📁 Arquivo: {output_file}\n"
        output += f"🎵 Músicas: {len(result)}\n"
        output += f"🎼 Tonalidade: {key or 'Qualquer uma'}\n"
        output += f"\n✅ Pronto para tocar!"
        
        self.pl_output_text.setText(output)
        QMessageBox.information(self, "Sucesso", f"Playlist criada: {output_file}")
    
    def _handle_sequence_playlist(self, output_file):
        """Cria playlist com sequência harmônica"""
        start_key = self.pl_seq_start.currentText()
        direction = self.pl_direction.currentText()
        seq_length = 8  # Default sequence length
        max_per_key = 3
        
        result = create_harmonic_sequence_playlist(
            input_directory=self.pl_input.text(),
            output_file=output_file,
            start_key=start_key,
            sequence_length=seq_length,
            direction=direction,
            max_songs_per_key=max_per_key
        )
        
        output = f"✅ Harmonic Sequence Playlist criada!\n"
        output += f"📁 Arquivo: {output_file}\n"
        output += f"🎵 Músicas: {len(result)}\n"
        output += f"🎼 Início: {start_key}\n"
        output += f"📍 Direção: {direction}\n"
        output += f"\n✅ Sequência harmônica criada!"
        
        self.pl_output_text.setText(output)
        QMessageBox.information(self, "Sucesso", f"Sequência criada: {output_file}")
    
    def _handle_transition_playlist(self, output_file):
        """Cria playlist de transição entre duas tonalidades"""
        start_key = self.pl_seq_start.currentText()
        target_key = self.pl_target_key.currentText()
        limit = self.pl_limit.value()
        
        result = create_key_to_key_playlist(
            input_directory=self.pl_input.text(),
            output_file=output_file,
            start_key=start_key,
            target_key=target_key,
            max_songs=limit
        )
        
        output = f"✅ Key Transition Playlist criada!\n"
        output += f"📁 Arquivo: {output_file}\n"
        output += f"🎵 Músicas: {len(result)}\n"
        output += f"🎼 Transição: {start_key} → {target_key}\n"
        output += f"\n✅ Transição harmônica criada!"
        
        self.pl_output_text.setText(output)
        QMessageBox.information(self, "Sucesso", f"Transição criada: {output_file}")
    
    def _handle_zone_playlist(self, output_file):
        """Cria playlist de zona compatível"""
        target_key = self.pl_key.currentText()
        if target_key == "Any":
            target_key = "8A"  # Default to 8A
        
        limit = self.pl_limit.value()
        
        result = create_camelot_zone_playlist(
            input_directory=self.pl_input.text(),
            output_file=output_file,
            target_key=target_key,
            zone_size=2,
            max_songs=limit
        )
        
        output = f"✅ Camelot Zone Playlist criada!\n"
        output += f"📁 Arquivo: {output_file}\n"
        output += f"🎵 Músicas: {len(result)}\n"
        output += f"🎼 Centro: {target_key}\n"
        output += f"\n✅ Todas as músicas são compatíveis!"
        
        self.pl_output_text.setText(output)
        QMessageBox.information(self, "Sucesso", f"Zona criada: {output_file}")

    
    def handle_compatibility(self):
        """Verifica compatibilidade"""
        try:
            key = self.compat_key.currentText()
            compatible = get_compatible_keys(key)
            
            output = f"🎼 Tonalidade selecionada: {key}\n"
            output += "─" * 50 + "\n\n"
            output += "🎵 Tonalidades compatíveis para mixagem harmônica:\n\n"
            
            if compatible:
                for i, k in enumerate(compatible, 1):
                    output += f"  {i}. {k}\n"
            else:
                output += f"  {key}\n"
            
            output += "\n💡 Dica: Chaves próximas no relógio Camelot"
            output += "\nharmonizam bem. Você pode misturar músicas"
            output += "\ndessas tonalidades sem choques harmônicos!"
            
            self.compat_output.setText(output)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro: {str(e)}")
    
    def clear_analyze_tab(self):
        """Limpa aba de análise"""
        self.analyze_file_input.clear()
        self.analyze_output.clear()
        self.selected_file = None
        self.analysis_results = []
    
    def clear_organize_tab(self):
        """Limpa aba de organização"""
        self.org_input.clear()
        self.org_output.clear()
        self.org_output_text.clear()
        self.move_files.setChecked(False)
        self.selected_input_folder = None
        self.selected_output_folder = None
    
    def clear_playlist_tab(self):
        """Limpa aba de playlist"""
        self.pl_input.clear()
        self.pl_output.setText("minha_playlist.m3u")
        self.pl_direction.setCurrentIndex(0)
        self.pl_bpm_min.setValue(0)
        self.pl_bpm_max.setValue(300)
        self.pl_energy.setCurrentIndex(0)
        self.pl_groove.setCurrentIndex(0)
        self.pl_limit.setValue(50)
        self.pl_output_text.clear()
        self.pl_mode_group.button(0).setChecked(True)


def main(language='ENG'):
    """
    Função principal
    
    Args:
        language (str): Initial language - 'ENG', 'PT', or 'ES' (default: 'ENG')
    """
    # Enable High-DPI / Retina display scaling before creating QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Ensure Camelot wheel image exists
    try:
        from utils.camelot_wheel_generator import generate_camelot_wheel
        assets_dir = get_assets_dir()
        wheel_path = assets_dir / "camelot_wheel.png"
        if not wheel_path.exists():
            generate_camelot_wheel(str(wheel_path))
    except Exception:
        pass  # If wheel generation fails, the UI will fall back to ASCII
    
    app = QApplication(sys.argv)
    window = DJAnalyzerGUI(language=language)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

