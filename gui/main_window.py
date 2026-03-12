"""
Main Window - Janela Principal da Aplicação (PyQt5)

Esta é a interface gráfica principal do DJ Harmonic Analyzer.
Implementada com PyQt5 para melhor compatibilidade e aparência profissional.
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QLineEdit, QFileDialog, QTextEdit,
    QComboBox, QSpinBox, QCheckBox, QMessageBox, QProgressDialog, QFrame,
    QRadioButton, QButtonGroup, QScrollArea, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QColor, QLinearGradient, QPalette, QPixmap
from PyQt5.QtSvg import QSvgWidget

from config import get_assets_dir
from audio_analysis.key_detection import analyze_track
from gui.file_manager.organizer import (
    find_audio_files, organize_by_key, create_harmonic_playlist,
    create_harmonic_sequence_playlist, create_key_to_key_playlist,
    create_camelot_zone_playlist
)
from utils.camelot_map import CAMELOT_MAP, get_compatible_keys
from utils.transition_scoring import calculate_transition_score
from utils.translations import Translator
from utils.dj_tips import DJTipsManager


class AnalysisWorker(QThread):
    """Worker thread para análise sem bloquear UI"""
    finished = pyqtSignal()
    result = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
    
    def run(self):
        try:
            result = analyze_track(self.file_path)
            self.result.emit(result)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit()


class DJAnalyzerGUI(QMainWindow):
    """Classe principal da interface gráfica com PyQt5 - CAMEL-HOT Theme"""
    
    def __init__(self, language='ENG'):
        super().__init__()
        self.translator = Translator(language)
        self.tips_manager = DJTipsManager(language)
        self.selected_file = None
        self.selected_input_folder = None
        self.selected_output_folder = None
        self.analysis_results = []  # Store multiple analysis results
        self.apply_theme()
        self.init_ui()
    
    def apply_theme(self):
        """Aplica tema desert sunset com cores do logo CAMEL-HOT - REFINED"""
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
            color: #404654;
            padding: 12px 28px;
            margin: 2px 2px 0px 2px;
            border-radius: 12px 12px 0px 0px;
            font-weight: 600;
            font-size: 13px;
            border: 1px solid rgba(232,216,65,0.3);
            border-bottom: none;
            letter-spacing: 0.4px;
            font-family: 'Inter', 'Roboto', 'Open Sans', sans-serif;
            min-width: 80px;
            text-align: center;
        }
        
        QTabBar::tab:selected {
            background: white;
            color: #1DB954;
            border: 1px solid #e8d841;
            border-bottom: 4px solid #e8d841;
            font-weight: 700;
            font-size: 12px;
        }
        
        QTabBar::tab:hover {
            background: #fafafa;
            color: #ff9500;
            border: 1px solid #ff9500;
        }
        
        QPushButton {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1, stop:0 #1DB954, stop:1 #16a844);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 14px 24px;
            font-weight: 600;
            font-size: 13px;
            font-family: 'Inter', 'Roboto', 'Open Sans', sans-serif;
            letter-spacing: 0.4px;
            box-shadow: 0 4px 12px rgba(29, 185, 84, 0.3);
        }
        
        QPushButton:hover {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1, stop:0 #1ed760, stop:1 #1aa34a);
            border: 1px solid rgba(30, 215, 96, 0.4);
            box-shadow: 0 6px 16px rgba(29, 185, 84, 0.4);
        }
        
        QPushButton:pressed {
            background: #1aa34a;
            padding: 13px 21px;
        }
        
        QLineEdit {
            background: white;
            color: #191414;
            border: 1px solid rgba(232,216,65,0.4);
            border-radius: 10px;
            padding: 12px 16px;
            font-size: 13px;
            font-family: 'Inter', 'Roboto', 'Open Sans', sans-serif;
            font-weight: 500;
        }
        
        QLineEdit:focus {
            border: 2px solid #ff9500;
            background: #fffef5;
        }
        
        QTextEdit {
            background: white;
            color: #191414;
            border: 1px solid rgba(232,216,65,0.3);
            border-radius: 10px;
            padding: 12px 16px;
            font-size: 12px;
            font-family: 'Inter', 'Roboto', monospace;
            line-height: 1.6;
            font-weight: 400;
        }
        
        QComboBox {
            background: white;
            color: #191414;
            border: 2px solid #e8d841;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 11px;
            font-family: 'Segoe UI', 'Roboto', sans-serif;
        }
        
        QComboBox:hover {
            border: 2px solid #ff9500;
        }
        
        QSpinBox {
            background: white;
            color: #191414;
            border: 2px solid #e8d841;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 11px;
            font-family: 'Segoe UI', 'Roboto', sans-serif;
        }
        
        QCheckBox {
            color: #191414;
            font-weight: 600;
            spacing: 8px;
            font-family: 'Segoe UI', 'Roboto', sans-serif;
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
            color: #191414;
        }
        
        QFrame {
            background: transparent;
            border: 1px solid rgba(232,216,65,0.2);
            border-radius: 8px;
        }
        
        QRadioButton {
            color: #191414;
            font-weight: 500;
            spacing: 6px;
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
        self.setStyleSheet(stylesheet)
        
        # Apply gradient background to main window
        palette = QPalette()
        gradient = QLinearGradient(0, 0, 1, 0)
        gradient.setCoordinateMode(QLinearGradient.StretchToDeviceMode)
        gradient.setColorAt(0.0, QColor("#1a4d2e"))
        gradient.setColorAt(0.25, QColor("#3d6e40"))
        gradient.setColorAt(0.4, QColor("#f4d03f"))
        gradient.setColorAt(0.65, QColor("#ff9500"))
        gradient.setColorAt(0.85, QColor("#f07c1e"))
        gradient.setColorAt(1.0, QColor("#c1440e"))
        
        palette.setBrush(QPalette.Background, gradient)
        self.setPalette(palette)
        self.setAutoFillBackground(True)
    
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
        self.setGeometry(100, 100, 900, 650)
        
        # Allow window to be resizable
        self.setMinimumSize(900, 500)
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
        
        # Logo container - supports SVG and image formats
        logo_container = QWidget()
        logo_layout = QVBoxLayout()
        logo_layout.setContentsMargins(0, 0, 0, 0)
        
        assets_dir = get_assets_dir()
        logo_found = False
        
        # Try to load image formats first (PNG, JPG), then SVG
        for logo_name in ["camel_mascot.png", "camel_mascot.jpg", "camel_mascot.jpeg", "camel_mascot.svg"]:
            logo_path = assets_dir / logo_name
            if logo_path.exists():
                if logo_name.endswith(".svg"):
                    logo_svg = QSvgWidget(str(logo_path))
                    logo_svg.setMinimumSize(100, 100)
                    logo_svg.setMaximumSize(100, 100)
                    logo_layout.addWidget(logo_svg)
                else:
                    logo_pixmap = QPixmap(str(logo_path))
                    logo_pixmap = logo_pixmap.scaledToWidth(100, Qt.SmoothTransformation)
                    logo_label = QLabel()
                    logo_label.setPixmap(logo_pixmap)
                    logo_label.setAlignment(Qt.AlignCenter)
                    logo_layout.addWidget(logo_label)
                logo_found = True
                break
        
        if not logo_found:
            # Placeholder if no logo found
            placeholder = QLabel("🐪")
            placeholder_font = QFont("Inter", 48)
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
        
        # Main title with gradient effect
        title = QLabel("CAMEL-HOT")
        title_font = QFont("Inter", 42, QFont.Bold)
        title_font.setLetterSpacing(QFont.PercentageSpacing, 110)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        # Split color effect: CAMEL in green, HOT in orange
        title.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #1a4d2e;
                font-weight: 900;
                font-size: 42px;
                letter-spacing: 3px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
            }
        """)
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
        title_layout.addWidget(tagline)
        
        title_widget.setLayout(title_layout)
        title_widget.setStyleSheet("background: transparent;")
        header_layout.addWidget(title_widget)
        header_layout.addStretch()
        
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
        header_layout.addWidget(lang_selector)
        
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
        
        # Tabs com estilo desert sunset
        tabs = QTabWidget()
        tabs.setDocumentMode(False)
        tabs.addTab(self.create_analyze_tab(), self.translator.get('tab_analyze'))
        tabs.addTab(self.create_organize_tab(), self.translator.get('tab_organize'))
        tabs.addTab(self.create_playlist_tab(), self.translator.get('tab_playlist'))
        tabs.addTab(self.create_compatibility_tab(), self.translator.get('tab_compatibility'))
        tabs.addTab(self.create_tips_tab(), self.translator.get('tab_tips'))
        tabs.addTab(self.create_camelot_wheel_tab(), "Camelot Wheel")
        tabs.addTab(self.create_about_tab(), self.translator.get('tab_about'))
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #e8d841;
                border-radius: 8px;
            }
            QTabBar {
                background: rgba(255, 255, 255, 0.9);
            }
        """)
        
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
        footer_layout.addWidget(footer_text)
        
        # Developer signature on the right
        developer_sig = QLabel("Design by H.Gwedez")
        developer_sig.setStyleSheet("color: #e8d841; font-weight: 500; font-size: 10px; font-style: italic; background: transparent;")
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
        """Cria aba para analisar música individual - IMPROVED LAYOUT"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(28, 28, 28, 28)
        
        # Título com estilo melhorado
        title = QLabel(self.translator.get('analyze_title'))
        title_font = QFont("Inter", 16, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #1DB954; letter-spacing: 0.5px;")
        layout.addWidget(title)
        
        # Linha decorativa
        sep_line = QFrame()
        sep_line.setFrameShape(QFrame.HLine)
        sep_line.setStyleSheet("background: #e8d841; height: 2px; border: none; margin: 8px 0px;")
        layout.addWidget(sep_line)
        
        # INPUT SECTION - Com melhor visual
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.95);
                border: 1px solid rgba(232,216,65,0.3);
                border-radius: 12px;
                padding: 18px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }
        """)
        input_layout = QVBoxLayout()
        input_layout.setSpacing(14)
        
        file_label = QLabel(self.translator.get('label_select_file'))
        file_label.setStyleSheet("font-weight: 700; color: #191414; font-size: 12px; letter-spacing: 0.3px;")
        input_layout.addWidget(file_label)
        
        file_row = QHBoxLayout()
        self.analyze_file_input = QLineEdit()
        self.analyze_file_input.setReadOnly(True)
        self.analyze_file_input.setPlaceholderText(self.translator.get('placeholder_audio_file'))
        self.analyze_file_input.setMinimumHeight(38)
        file_row.addWidget(self.analyze_file_input)
        
        browse_btn = QPushButton(self.translator.get('btn_browse'))
        browse_btn.setMaximumWidth(110)
        browse_btn.setMinimumHeight(38)
        browse_btn.clicked.connect(self.browse_analyze_file)
        file_row.addWidget(browse_btn)
        input_layout.addLayout(file_row)
        
        input_frame.setLayout(input_layout)
        layout.addWidget(input_frame)
        
        # ACTION BUTTONS - Improved styling
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        analyze_btn = QPushButton(self.translator.get('btn_analyze_track'))
        analyze_btn.setMinimumHeight(48)
        analyze_btn.setMinimumWidth(200)
        analyze_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        analyze_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1,
                    stop:0 #3B82F6,
                    stop:1 #1D4ED8
                );
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-weight: 600;
                letter-spacing: 0.4px;
            }
            QPushButton:hover {
                background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1,
                    stop:0 #60A5FA,
                    stop:1 #2563EB
                );
            }
        """)
        analyze_btn.clicked.connect(self.handle_analyze)
        btn_layout.addWidget(analyze_btn)
        
        clear_btn = QPushButton(self.translator.get('btn_clear'))
        clear_btn.setMaximumWidth(120)
        clear_btn.setMinimumHeight(48)
        clear_btn.setStyleSheet("""
            QPushButton {
                background: #EF4444;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }
            QPushButton:hover {
                background: #DC2626;
            }
        """)
        clear_btn.clicked.connect(lambda: self.clear_analyze_tab())
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # RESULTS SECTION - Expanded area with frame
        results_frame = QFrame()
        results_frame.setStyleSheet("""
            QFrame {
                background: rgba(255,255,255,0.95);
                border: 1px solid rgba(232,216,65,0.3);
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
        """)
        results_layout = QVBoxLayout()
        results_layout.setContentsMargins(0,0,0,0)
        results_layout.setSpacing(8)
        results_label = QLabel(self.translator.get('label_results'))
        results_label.setStyleSheet("font-weight: 700; color: #191414; font-size: 14px; letter-spacing: 0.5px;")
        results_layout.addWidget(results_label)
        results_frame.setLayout(results_layout)
        layout.addWidget(results_frame)
        
        self.analyze_output = QTextEdit()
        self.analyze_output.setReadOnly(True)
        self.analyze_output.setMinimumHeight(100)
        self.analyze_output.setStyleSheet("""
            QTextEdit {
                background: white;
                border: 1px solid rgba(232,216,65,0.3);
                border-radius: 12px;
                padding: 16px;
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
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title = QLabel(self.translator.get('organize_title'))
        title_font = QFont("Segoe UI", 14, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #1DB954;")
        layout.addWidget(title)
        
        # Input folder
        input_layout = QHBoxLayout()
        input_label = QLabel(self.translator.get('label_input_folder'))
        input_label.setStyleSheet("font-weight: 600; color: #191414;")
        input_layout.addWidget(input_label)
        self.org_input = QLineEdit()
        self.org_input.setReadOnly(True)
        self.org_input.setPlaceholderText(self.translator.get('placeholder_music_source'))
        input_layout.addWidget(self.org_input)
        browse_in = QPushButton(self.translator.get('btn_browse'))
        browse_in.setMaximumWidth(100)
        browse_in.clicked.connect(self.browse_org_input)
        input_layout.addWidget(browse_in)
        layout.addLayout(input_layout)
        
        # Output folder
        output_layout = QHBoxLayout()
        output_label = QLabel(self.translator.get('label_output_folder'))
        output_label.setStyleSheet("font-weight: 600; color: #191414;")
        output_layout.addWidget(output_label)
        self.org_output = QLineEdit()
        self.org_output.setReadOnly(True)
        self.org_output.setPlaceholderText(self.translator.get('placeholder_destination'))
        output_layout.addWidget(self.org_output)
        browse_out = QPushButton(self.translator.get('btn_browse'))
        browse_out.setMaximumWidth(100)
        browse_out.clicked.connect(self.browse_org_output)
        output_layout.addWidget(browse_out)
        layout.addLayout(output_layout)
        
        # Checkbox mover
        self.move_files = QCheckBox(self.translator.get('checkbox_move_files'))
        layout.addWidget(self.move_files)
        layout.addWidget(QLabel(self.translator.get('warning_move_files')))
        
        # Botões
        btn_layout = QHBoxLayout()
        organize_btn = QPushButton(self.translator.get('btn_organize_library'))
        organize_btn.setMinimumHeight(40)
        organize_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        organize_btn.setStyleSheet("""
            QPushButton {
                background: #FF9500;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background: #FFA500;
            }
        """)
        organize_btn.clicked.connect(self.handle_organize)
        btn_layout.addWidget(organize_btn)
        
        clear_btn = QPushButton(self.translator.get('btn_clear'))
        clear_btn.setMaximumWidth(100)
        clear_btn.clicked.connect(lambda: self.clear_organize_tab())
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)
        
        # Output
        layout.addWidget(QLabel(self.translator.get('label_progress')))
        self.org_output_text = QTextEdit()
        self.org_output_text.setReadOnly(True)
        self.org_output_text.setMinimumHeight(200)
        layout.addWidget(self.org_output_text)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_playlist_tab(self):
        """Cria aba para criar playlist"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title = QLabel(self.translator.get('playlist_title'))
        title_font = QFont("Segoe UI", 14, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #1DB954;")
        layout.addWidget(title)
        
        # Playlist type selection
        layout.addWidget(QLabel(self.translator.get('label_playlist_mode')))
        self.pl_mode_group = QButtonGroup()
        mode_layout = QHBoxLayout()
        
        mode_simple = QRadioButton(self.translator.get('mode_simple_harmonic'))
        mode_sequence = QRadioButton(self.translator.get('mode_harmonic_sequence'))
        mode_transition = QRadioButton(self.translator.get('mode_key_transition'))
        mode_zone = QRadioButton(self.translator.get('mode_camelot_zone'))
        
        self.pl_mode_group.addButton(mode_simple, 0)
        self.pl_mode_group.addButton(mode_sequence, 1)
        self.pl_mode_group.addButton(mode_transition, 2)
        self.pl_mode_group.addButton(mode_zone, 3)
        
        mode_simple.setChecked(True)
        
        mode_layout.addWidget(mode_simple)
        mode_layout.addWidget(mode_sequence)
        mode_layout.addWidget(mode_transition)
        mode_layout.addWidget(mode_zone)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # Input folder
        input_layout = QHBoxLayout()
        input_label = QLabel(self.translator.get('label_music_folder'))
        input_label.setStyleSheet("font-weight: 600; color: #191414;")
        input_layout.addWidget(input_label)
        self.pl_input = QLineEdit()
        self.pl_input.setReadOnly(True)
        self.pl_input.setPlaceholderText(self.translator.get('placeholder_select_music'))
        input_layout.addWidget(self.pl_input)
        browse_in = QPushButton(self.translator.get('btn_browse'))
        browse_in.setMaximumWidth(100)
        browse_in.clicked.connect(self.browse_pl_input)
        input_layout.addWidget(browse_in)
        layout.addLayout(input_layout)
        
        # Output file
        output_layout = QHBoxLayout()
        output_label = QLabel(self.translator.get('label_playlist_filename'))
        output_label.setStyleSheet("font-weight: 600; color: #191414;")
        output_layout.addWidget(output_label)
        self.pl_output = QLineEdit("my_playlist.m3u")
        output_layout.addWidget(self.pl_output)
        layout.addLayout(output_layout)
        
        # Mode-specific options section
        layout.addWidget(QLabel(self.translator.get('label_options')))
        
        # Simple & Zone modes: Camelot Key
        simple_zone_layout = QHBoxLayout()
        simple_zone_layout.addWidget(QLabel(self.translator.get('label_camelot_key')))
        self.pl_key = QComboBox()
        self.pl_key.addItem("Any")
        self.pl_key.addItems(sorted(set(CAMELOT_MAP.values())))
        simple_zone_layout.addWidget(self.pl_key)
        
        # Sequence mode: Start key + direction
        simple_zone_layout.addSpacing(20)
        simple_zone_layout.addWidget(QLabel(self.translator.get('label_sequence_start')))
        self.pl_seq_start = QComboBox()
        self.pl_seq_start.addItems(sorted(set(CAMELOT_MAP.values())))
        self.pl_seq_start.setCurrentText("8A")
        simple_zone_layout.addWidget(self.pl_seq_start)
        
        simple_zone_layout.addWidget(QLabel(self.translator.get('label_direction')))
        self.pl_direction = QComboBox()
        self.pl_direction.addItems(["forward", "backward", "zigzag"])
        simple_zone_layout.addWidget(self.pl_direction)
        
        # Transition mode: Start + End keys
        simple_zone_layout.addSpacing(20)
        simple_zone_layout.addWidget(QLabel(self.translator.get('label_transition_end')))
        self.pl_target_key = QComboBox()
        self.pl_target_key.addItems(sorted(set(CAMELOT_MAP.values())))
        self.pl_target_key.setCurrentText("3B")
        simple_zone_layout.addWidget(self.pl_target_key)
        
        layout.addLayout(simple_zone_layout)
        
        # BPM filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel(self.translator.get('label_min_bpm')))
        self.pl_bpm_min = QSpinBox()
        self.pl_bpm_min.setMinimum(0)
        self.pl_bpm_min.setMaximum(300)
        filter_layout.addWidget(self.pl_bpm_min)
        
        filter_layout.addWidget(QLabel(self.translator.get('label_max_bpm')))
        self.pl_bpm_max = QSpinBox()
        self.pl_bpm_max.setMinimum(0)
        self.pl_bpm_max.setMaximum(300)
        self.pl_bpm_max.setValue(300)
        filter_layout.addWidget(self.pl_bpm_max)
        
        filter_layout.addWidget(QLabel("Limit:"))
        self.pl_limit = QSpinBox()
        self.pl_limit.setMinimum(1)
        self.pl_limit.setMaximum(1000)
        self.pl_limit.setValue(50)
        filter_layout.addWidget(self.pl_limit)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Botões
        btn_layout = QHBoxLayout()
        create_btn = QPushButton(self.translator.get('btn_create_playlist'))
        create_btn.setMinimumHeight(40)
        create_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        create_btn.setStyleSheet("""
            QPushButton {
                background: #1DB954;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background: #1ed760;
            }
        """)
        create_btn.clicked.connect(self.handle_playlist)
        btn_layout.addWidget(create_btn)
        
        clear_btn = QPushButton(self.translator.get('btn_clear'))
        clear_btn.setMaximumWidth(100)
        clear_btn.clicked.connect(lambda: self.clear_playlist_tab())
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)
        
        # Output
        layout.addWidget(QLabel("Result:"))
        self.pl_output_text = QTextEdit()
        self.pl_output_text.setReadOnly(True)
        self.pl_output_text.setMinimumHeight(150)
        layout.addWidget(self.pl_output_text)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_compatibility_tab(self):
        """Cria aba para verificar compatibilidade"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title = QLabel(self.translator.get('compatibility_title'))
        title_font = QFont("Segoe UI", 14, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #1DB954;")
        layout.addWidget(title)
        
        # SECTION 1: Transition Comparison
        layout.addWidget(QLabel("-" * 70))
        layout.addWidget(QLabel("Transition Comparison"))
        
        # Track 1 selection
        file1_layout = QHBoxLayout()
        file1_label = QLabel("Track 1:")
        file1_label.setStyleSheet("font-weight: 600; color: #191414;")
        file1_layout.addWidget(file1_label)
        self.compat_file1 = QLineEdit()
        self.compat_file1.setReadOnly(True)
        self.compat_file1.setPlaceholderText("Choose first track...")
        file1_layout.addWidget(self.compat_file1)
        browse1_btn = QPushButton(self.translator.get('btn_browse'))
        browse1_btn.setMaximumWidth(80)
        browse1_btn.clicked.connect(self.browse_compat_file1)
        file1_layout.addWidget(browse1_btn)
        layout.addLayout(file1_layout)
        
        # Track 2 selection
        file2_layout = QHBoxLayout()
        file2_label = QLabel("Track 2:")
        file2_label.setStyleSheet("font-weight: 600; color: #191414;")
        file2_layout.addWidget(file2_label)
        self.compat_file2 = QLineEdit()
        self.compat_file2.setReadOnly(True)
        self.compat_file2.setPlaceholderText("Choose second track...")
        file2_layout.addWidget(self.compat_file2)
        browse2_btn = QPushButton(self.translator.get('btn_browse'))
        browse2_btn.setMaximumWidth(80)
        browse2_btn.clicked.connect(self.browse_compat_file2)
        file2_layout.addWidget(browse2_btn)
        layout.addLayout(file2_layout)
        
        # Compare button
        compare_layout = QHBoxLayout()
        compare_btn = QPushButton("Compare Tracks")
        compare_btn.setMinimumHeight(40)
        compare_btn.setMinimumWidth(200)
        compare_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        compare_btn.setStyleSheet("""
            QPushButton {
                background: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background: #2563EB;
            }
        """)
        compare_btn.clicked.connect(self.handle_transition_comparison)
        compare_layout.addWidget(compare_btn)
        compare_layout.addStretch()
        layout.addLayout(compare_layout)
        
        layout.addWidget(QLabel(""))
        
        # SECTION 2: Key Compatibility
        layout.addWidget(QLabel("-" * 70))
        layout.addWidget(QLabel("Camelot Key Compatibility"))
        
        # Seleção
        key_layout = QHBoxLayout()
        key_label = QLabel("Select Camelot Key:")
        key_label.setStyleSheet("font-weight: 600; color: #191414;")
        key_layout.addWidget(key_label)
        self.compat_key = QComboBox()
        self.compat_key.addItems(sorted(set(CAMELOT_MAP.values())))
        self.compat_key.setCurrentText("8A")
        key_layout.addWidget(self.compat_key)
        key_layout.addStretch()
        layout.addLayout(key_layout)
        
        # Botões
        btn_layout = QHBoxLayout()
        check_btn = QPushButton(self.translator.get('btn_check_compatibility'))
        check_btn.setMinimumHeight(40)
        check_btn.setMinimumWidth(200)
        check_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        check_btn.setStyleSheet("""
            QPushButton {
                background: #FF9500;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background: #FFA500;
            }
        """)
        check_btn.clicked.connect(self.handle_compatibility)
        btn_layout.addWidget(check_btn)
        
        clear_btn = QPushButton(self.translator.get('btn_clear'))
        clear_btn.setMaximumWidth(100)
        clear_btn.clicked.connect(lambda: self.compat_output.clear())
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Output
        layout.addWidget(QLabel(self.translator.get('label_results')))
        self.compat_output = QTextEdit()
        self.compat_output.setReadOnly(True)
        self.compat_output.setMinimumHeight(300)
        self.compat_output.setStyleSheet("background: white; border: 1px solid #D1D5DB; border-radius: 6px;")
        layout.addWidget(self.compat_output)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_tips_tab(self):
        """Cria aba de Dicas de DJ"""
        widget = QWidget()
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
        
        # Tip Display Area
        tip_frame = QFrame()
        tip_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(spread:pad, x1:0 y1:0, x2:1 y2:1,
                    stop:0 #f9fafb,
                    stop:1 #f3f4f6
                );
                border: 3px solid #e8d841;
                border-radius: 12px;
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
        
        # Tip Counter (shows which tip we're on)
        counter_layout = QHBoxLayout()
        counter_layout.addStretch()
        self.tip_counter = QLabel()
        self.tip_counter.setFont(QFont("Segoe UI", 10))
        self.tip_counter.setStyleSheet("color: #666;")
        counter_layout.addWidget(self.tip_counter)
        counter_layout.addStretch()
        layout.addLayout(counter_layout)
        
        # Button Layout
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        next_tip_btn = QPushButton(self.translator.get('btn_next_tip'))
        next_tip_btn.setMinimumHeight(40)
        next_tip_btn.setMinimumWidth(200)
        next_tip_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        next_tip_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1,
                    stop:0 #1DB954,
                    stop:1 #16a844
                );
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1,
                    stop:0 #1ed760,
                    stop:1 #1aa34a
                );
            }
            QPushButton:pressed {
                background: #1aa34a;
            }
        """)
        next_tip_btn.clicked.connect(self.show_next_tip)
        btn_layout.addWidget(next_tip_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        widget.setLayout(layout)
        
        # Load the first tip when tab is created
        self.show_next_tip()
        
        return widget
    
    def show_next_tip(self):
        """Display the next random tip"""
        tip_text = self.tips_manager.get_random_tip()
        self.tip_label.setText(tip_text)
        
        # Update counter
        total_tips = self.tips_manager.get_tip_count()
        tip_index = self.tips_manager.last_tip_index + 1
        self.tip_counter.setText(f"Tip {tip_index} of {total_tips}")
    
    def create_camelot_wheel_tab(self):
        """Cria aba dedicada à Roda Camelot - Nova Tab"""
        widget = QWidget()
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
            wheel_display.setStyleSheet("color: #333; background: white; padding: 20px; border-radius: 8px; line-height: 1.6;")
            wheel_layout.addWidget(wheel_display)
        
        # Description
        wheel_layout.addSpacing(12)
        desc_label = QLabel(wheel_desc)
        desc_label.setFont(QFont("Segoe UI", 12))
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #404654; max-width: 600px; line-height: 1.6;")
        wheel_layout.addWidget(desc_label)
        
        wheel_section.setLayout(wheel_layout)
        content_layout.addWidget(wheel_section)
        
        # ===== KEY INFO SECTION =====
        info_section = QFrame()
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
        key_info_label.setStyleSheet("color: #191414; line-height: 1.8;")
        info_layout.addWidget(key_info_label)
        
        info_section.setLayout(info_layout)
        content_layout.addWidget(info_section)
        
        # ===== MIXING TIPS SECTION =====
        tips_section = QFrame()
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
        tips_title_label.setStyleSheet("color: #191414; margin-bottom: 10px;")
        tips_layout.addWidget(tips_title_label)
        
        tips_text_label = QLabel(tips_text)
        tips_text_label.setFont(QFont("Segoe UI", 11))
        tips_text_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        tips_text_label.setWordWrap(True)
        tips_text_label.setStyleSheet("color: #404654; line-height: 1.8;")
        tips_layout.addWidget(tips_text_label)
        
        tips_section.setLayout(tips_layout)
        content_layout.addWidget(tips_section)
        
        content_layout.addStretch()
        scroll_content.setLayout(content_layout)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        widget.setLayout(main_layout)
        return widget
    
    def create_about_tab(self):
        """Cria aba Sobre - IMPROVED com clarificação offline"""
        widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)
        
        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(18)
        
        # ===== APP INFO SECTION =====
        app_info = QTextEdit()
        app_info.setReadOnly(True)
        app_info.setStyleSheet("""
            QTextEdit {
                background: white;
                border: 3px solid #1DB954;
                border-radius: 12px;
                padding: 20px;
                font-size: 12px;
                line-height: 1.6;
            }
        """)
        
        # Get language-specific about content
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
        else:  # ENG (default)
            about_content = """
CAMEL-HOT - Harmonic Music Analyzer v2.0

═════════════════════════════════════════════════════════════

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
        content_layout.addWidget(app_info)
        
        scroll_content.setLayout(content_layout)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        widget.setLayout(main_layout)
        return widget
    
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
        
        try:
            # Analyze both tracks
            track1 = analyze_track(self.compat_file1_path)
            track2 = analyze_track(self.compat_file2_path)
            
            # Calculate transition score
            transition = calculate_transition_score(track1, track2)
            
            # Build output
            output = "🎛️ TRANSITION COMPARISON\n"
            output += "═" * 70 + "\n\n"
            
            # Track info
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
            
            # Transition scores
            output += "┌─ TRANSITION COMPATIBILITY SCORES\n"
            output += f"│  Overall:   {transition.get('overall_score', 0):.2f}/1.0  {transition.get('recommendation', '')}\n"
            output += f"│  Harmonic:  {transition.get('harmonic_score', 0):.2f}  (Camelot wheel)\n"
            output += f"│  Energy:    {transition.get('energy_score', 0):.2f}  (Spectral shift)\n"
            output += f"│  Groove:    {transition.get('groove_score', 0):.2f}  (Rhythm match)\n"
            output += f"│  Mood:      {transition.get('mood_score', 0):.2f}  (Emotional fit)\n"
            output += f"│  BPM:       {transition.get('bpm_score', 0):.2f}  (Tempo match)\n"
            output += "└─\n\n"
            
            # Recommendations
            output += "💡 NOTES:\n"
            for note in transition.get('notes', []):
                output += f"   {note}\n"
            
            output += "\n" + "═" * 70 + "\n"
            
            self.compat_output.setText(output)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao comparar:\n{str(e)}")
    
    def handle_analyze(self):
        """Analisa um arquivo"""
        if not self.selected_file:
            QMessageBox.warning(self, "Aviso", "Selecione um arquivo!")
            return
        
        try:
            result = analyze_track(self.selected_file)
            
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
            QMessageBox.critical(self, "Erro", f"Erro ao analisar:\n{str(e)}")
    
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
        """Organiza biblioteca"""
        if not self.selected_input_folder or not self.selected_output_folder:
            QMessageBox.warning(self, "Aviso", "Selecione ambas as pastas!")
            return
        
        try:
            self.org_output_text.setText("🔄 Iniciando organização...\n")
            self.org_output_text.repaint()
            
            audio_files = find_audio_files(self.selected_input_folder)
            self.org_output_text.setText(f"🎵 Encontrados {len(audio_files)} arquivos\n")
            self.org_output_text.repaint()
            
            result = organize_by_key(
                self.selected_input_folder,
                self.selected_output_folder,
                move_files=self.move_files.isChecked()
            )
            
            output = f"✅ Total de arquivos: {result.get('total_files', 0)}\n"
            output += f"✅ Organizados: {result.get('organized_count', 0)}\n"
            output += f"\n📁 Estrutura criada em:\n{self.selected_output_folder}\n\n"
            
            if result.get('by_key'):
                output += "Distribuição por tonalidade:\n"
                for key in sorted(result.get('by_key', {}).keys()):
                    count = len(result.get('by_key', {})[key])
                    output += f"  • {key}: {count} músicas\n"
            
            output += "\n✅ Organização concluída!"
            self.org_output_text.setText(output)
            
            QMessageBox.information(self, "Sucesso", "Biblioteca organizada com sucesso!")
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao organizar:\n{str(e)}")
    
    def handle_playlist(self):
        """Cria playlist baseado no modo selecionado"""
        if not self.pl_input.text():
            QMessageBox.warning(self, "Aviso", "Selecione uma pasta!")
            return
        
        try:
            output_file = self.pl_output.text()
            if not output_file.endswith('.m3u'):
                output_file += '.m3u'
            
            mode = self.pl_mode_group.checkedId()
            self.pl_output_text.setText("🔄 Criando playlist...\n")
            self.pl_output_text.repaint()
            
            if mode == 0:  # Simple Harmonic
                self._handle_simple_playlist(output_file)
            elif mode == 1:  # Harmonic Sequence
                self._handle_sequence_playlist(output_file)
            elif mode == 2:  # Key Transition
                self._handle_transition_playlist(output_file)
            elif mode == 3:  # Camelot Zone
                self._handle_zone_playlist(output_file)
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao criar playlist:\n{str(e)}")
    
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
        self.pl_key.setCurrentIndex(0)
        self.pl_seq_start.setCurrentText("8A")
        self.pl_target_key.setCurrentText("3B")
        self.pl_direction.setCurrentIndex(0)
        self.pl_bpm_min.setValue(0)
        self.pl_bpm_max.setValue(300)
        self.pl_limit.setValue(50)
        self.pl_output_text.clear()
        self.pl_mode_group.button(0).setChecked(True)


def main(language='ENG'):
    """
    Função principal
    
    Args:
        language (str): Initial language - 'ENG', 'PT', or 'ES' (default: 'ENG')
    """
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

