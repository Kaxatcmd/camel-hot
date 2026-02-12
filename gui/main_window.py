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
    QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QColor, QLinearGradient, QPalette, QPixmap
from PyQt5.QtSvg import QSvgWidget

from audio_analysis.key_detection import analyze_track
from file_manager.organizaer import (
    find_audio_files, organize_by_key, create_harmonic_playlist,
    create_harmonic_sequence_playlist, create_key_to_key_playlist,
    create_camelot_zone_playlist
)
from utils.camelot_map import CAMELOT_MAP, get_compatible_keys


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
    
    def __init__(self):
        super().__init__()
        self.selected_file = None
        self.selected_input_folder = None
        self.selected_output_folder = None
        self.analysis_results = {}
        self.apply_theme()
        self.init_ui()
    
    def apply_theme(self):
        """Aplica tema desert sunset com cores do logo CAMEL-HOT"""
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
        
        QTabWidget {
            background: white;
            border-radius: 12px;
        }
        
        QTabWidget::pane {
            border: 2px solid #e8d841;
            background: white;
            border-radius: 12px;
            margin-top: -2px;
        }
        
        QTabBar::tab {
            background: linear-gradient(180deg, #f5f5f5 0%, #efefef 100%);
            color: #333;
            padding: 12px 24px;
            margin: 2px 2px 0px 2px;
            border-radius: 10px 10px 0px 0px;
            font-weight: 600;
            font-size: 11px;
            border: 1px solid #ddd;
            border-bottom: none;
        }
        
        QTabBar::tab:selected {
            background: white;
            color: #1DB954;
            border: 1px solid #e8d841;
            border-bottom: 3px solid #e8d841;
            font-weight: 700;
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
            border-radius: 8px;
            padding: 10px 18px;
            font-weight: 600;
            font-size: 11px;
        }
        
        QPushButton:hover {
            background: qlineargradient(spread:pad, x1:0 y1:0, x2:0 y2:1, stop:0 #1ed760, stop:1 #1aa34a);
        }
        
        QPushButton:pressed {
            background: #1aa34a;
        }
        
        QLineEdit {
            background: white;
            color: #191414;
            border: 2px solid #e8d841;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 11px;
        }
        
        QLineEdit:focus {
            border: 2px solid #ff9500;
            background: #fffef5;
        }
        
        QTextEdit {
            background: white;
            color: #191414;
            border: 2px solid #e8d841;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 10px;
            font-family: 'Courier New';
        }
        
        QComboBox {
            background: white;
            color: #191414;
            border: 2px solid #e8d841;
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 10px;
        }
        
        QComboBox:hover {
            border: 2px solid #ff9500;
        }
        
        QSpinBox {
            background: white;
            color: #191414;
            border: 2px solid #e8d841;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 10px;
        }
        
        QCheckBox {
            color: #191414;
            font-weight: 600;
            spacing: 8px;
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
        self.setWindowTitle("CAMEL-HOT - Harmonic Music Analyzer")
        self.setGeometry(100, 100, 1000, 800)
        
        # Widget central
        central_widget = QWidget()
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
        
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        logo_found = False
        
        # Try to load image formats first (PNG, JPG), then SVG
        for logo_name in ["camel_mascot.png", "camel_mascot.jpg", "camel_mascot.jpeg", "camel_mascot.svg"]:
            logo_path = os.path.join(assets_dir, logo_name)
            if os.path.exists(logo_path):
                if logo_name.endswith(".svg"):
                    logo_svg = QSvgWidget(logo_path)
                    logo_svg.setMinimumSize(100, 100)
                    logo_svg.setMaximumSize(100, 100)
                    logo_layout.addWidget(logo_svg)
                else:
                    logo_pixmap = QPixmap(logo_path)
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
            placeholder_font = QFont("Arial", 48)
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
        title_font = QFont("Arial", 42, QFont.Bold)
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
        subtitle = QLabel("Harmonic Music Analyzer")
        subtitle_font = QFont("Arial", 11, QFont.Bold)
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
        tagline = QLabel("Mix by Harmony, Not by Chance")
        tagline_font = QFont("Arial", 9)
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
        tabs.addTab(self.create_analyze_tab(), "Analyze")
        tabs.addTab(self.create_organize_tab(), "Organize")
        tabs.addTab(self.create_playlist_tab(), "Playlist")
        tabs.addTab(self.create_compatibility_tab(), "Compatibility")
        tabs.addTab(self.create_about_tab(), "About")
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #e8d841;
                border-radius: 8px;
            }
            QTabBar {
                background: rgba(255, 255, 255, 0.9);
            }
        """)
        
        main_layout.addWidget(tabs)
        
        # Rodapé com botão sair (desert sunset styled)
        footer_layout = QHBoxLayout()
        
        # Texto do rodapé em branco para bom contraste
        footer_text = QLabel("Design for DJ's and Electronic Music Producers.")
        footer_text.setStyleSheet("color: #ffffff; font-weight: 500; font-size: 10px;")
        footer_layout.addWidget(footer_text)
        footer_layout.addStretch()
        
        exit_btn = QPushButton("Exit")
        exit_btn.setMinimumHeight(40)
        exit_btn.setMinimumWidth(100)
        exit_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    spread:pad, x1:0 y1:0, x2:1 y2:1,
                    stop:0 #ff9500,
                    stop:1 #c1440e
                );
                color: white;
                border: 2px solid #f07c1e;
                border-radius: 8px;
                padding: 10px;
                font-weight: 700;
                font-size: 11px;
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
        
        main_layout.addLayout(footer_layout)
        
        central_widget.setLayout(main_layout)
    
    
    def create_analyze_tab(self):
        """Cria aba para analisar música individual"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title = QLabel("Analyze Individual Track")
        title_font = QFont("Segoe UI", 14, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #1DB954;")
        layout.addWidget(title)
        
        # Seleção de arquivo
        file_layout = QHBoxLayout()
        file_label = QLabel("Select file:")
        file_label.setStyleSheet("font-weight: 600; color: #191414;")
        file_layout.addWidget(file_label)
        self.analyze_file_input = QLineEdit()
        self.analyze_file_input.setReadOnly(True)
        self.analyze_file_input.setPlaceholderText("Choose an audio file...")
        file_layout.addWidget(self.analyze_file_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.setMaximumWidth(100)
        browse_btn.clicked.connect(self.browse_analyze_file)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        analyze_btn = QPushButton("Analyze Track")
        analyze_btn.setMinimumHeight(40)
        analyze_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        analyze_btn.setStyleSheet("""
            QPushButton {
                background: #3B82F6;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #2563EB;
            }
        """)
        analyze_btn.clicked.connect(self.handle_analyze)
        btn_layout.addWidget(analyze_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setMaximumWidth(100)
        clear_btn.clicked.connect(lambda: self.clear_analyze_tab())
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)
        
        # Output
        layout.addWidget(QLabel("Results:"))
        self.analyze_output = QTextEdit()
        self.analyze_output.setReadOnly(True)
        self.analyze_output.setMinimumHeight(250)
        self.analyze_output.setStyleSheet("background: white; border: 1px solid #D1D5DB; border-radius: 6px;")
        layout.addWidget(self.analyze_output)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_organize_tab(self):
        """Cria aba para organizar biblioteca"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title = QLabel("Organize Music Library")
        title_font = QFont("Segoe UI", 14, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #1DB954;")
        layout.addWidget(title)
        
        # Input folder
        input_layout = QHBoxLayout()
        input_label = QLabel("Input folder:")
        input_label.setStyleSheet("font-weight: 600; color: #191414;")
        input_layout.addWidget(input_label)
        self.org_input = QLineEdit()
        self.org_input.setReadOnly(True)
        self.org_input.setPlaceholderText("Choose music source folder...")
        input_layout.addWidget(self.org_input)
        browse_in = QPushButton("Browse")
        browse_in.setMaximumWidth(100)
        browse_in.clicked.connect(self.browse_org_input)
        input_layout.addWidget(browse_in)
        layout.addLayout(input_layout)
        
        # Output folder
        output_layout = QHBoxLayout()
        output_label = QLabel("Output folder:")
        output_label.setStyleSheet("font-weight: 600; color: #191414;")
        output_layout.addWidget(output_label)
        self.org_output = QLineEdit()
        self.org_output.setReadOnly(True)
        self.org_output.setPlaceholderText("Choose destination folder...")
        output_layout.addWidget(self.org_output)
        browse_out = QPushButton("Browse")
        browse_out.setMaximumWidth(100)
        browse_out.clicked.connect(self.browse_org_output)
        output_layout.addWidget(browse_out)
        layout.addLayout(output_layout)
        
        # Checkbox mover
        self.move_files = QCheckBox("Move files (instead of copying)")
        layout.addWidget(self.move_files)
        layout.addWidget(QLabel("⚠️  Warning: Original files will be moved!"))
        
        # Botões
        btn_layout = QHBoxLayout()
        organize_btn = QPushButton("Organize Library")
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
        
        clear_btn = QPushButton("Clear")
        clear_btn.setMaximumWidth(100)
        clear_btn.clicked.connect(lambda: self.clear_organize_tab())
        btn_layout.addWidget(clear_btn)
        layout.addLayout(btn_layout)
        
        # Output
        layout.addWidget(QLabel("Progress:"))
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
        title = QLabel("Create Harmonic Playlist")
        title_font = QFont("Segoe UI", 14, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #1DB954;")
        layout.addWidget(title)
        
        # Playlist type selection
        layout.addWidget(QLabel("Playlist Mode:"))
        self.pl_mode_group = QButtonGroup()
        mode_layout = QHBoxLayout()
        
        mode_simple = QRadioButton("Simple Harmonic")
        mode_sequence = QRadioButton("Harmonic Sequence")
        mode_transition = QRadioButton("Key Transition")
        mode_zone = QRadioButton("Camelot Zone")
        
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
        input_label = QLabel("Music folder:")
        input_label.setStyleSheet("font-weight: 600; color: #191414;")
        input_layout.addWidget(input_label)
        self.pl_input = QLineEdit()
        self.pl_input.setReadOnly(True)
        self.pl_input.setPlaceholderText("Select music folder...")
        input_layout.addWidget(self.pl_input)
        browse_in = QPushButton("Browse")
        browse_in.setMaximumWidth(100)
        browse_in.clicked.connect(self.browse_pl_input)
        input_layout.addWidget(browse_in)
        layout.addLayout(input_layout)
        
        # Output file
        output_layout = QHBoxLayout()
        output_label = QLabel("Playlist filename:")
        output_label.setStyleSheet("font-weight: 600; color: #191414;")
        output_layout.addWidget(output_label)
        self.pl_output = QLineEdit("my_playlist.m3u")
        output_layout.addWidget(self.pl_output)
        layout.addLayout(output_layout)
        
        # Mode-specific options section
        layout.addWidget(QLabel("Options (depends on mode):"))
        
        # Simple & Zone modes: Camelot Key
        simple_zone_layout = QHBoxLayout()
        simple_zone_layout.addWidget(QLabel("Camelot Key:"))
        self.pl_key = QComboBox()
        self.pl_key.addItem("Any")
        self.pl_key.addItems(sorted(set(CAMELOT_MAP.values())))
        simple_zone_layout.addWidget(self.pl_key)
        
        # Sequence mode: Start key + direction
        simple_zone_layout.addSpacing(20)
        simple_zone_layout.addWidget(QLabel("Sequence Start:"))
        self.pl_seq_start = QComboBox()
        self.pl_seq_start.addItems(sorted(set(CAMELOT_MAP.values())))
        self.pl_seq_start.setCurrentText("8A")
        simple_zone_layout.addWidget(self.pl_seq_start)
        
        simple_zone_layout.addWidget(QLabel("Direction:"))
        self.pl_direction = QComboBox()
        self.pl_direction.addItems(["forward", "backward", "zigzag"])
        simple_zone_layout.addWidget(self.pl_direction)
        
        # Transition mode: Start + End keys
        simple_zone_layout.addSpacing(20)
        simple_zone_layout.addWidget(QLabel("Transition End:"))
        self.pl_target_key = QComboBox()
        self.pl_target_key.addItems(sorted(set(CAMELOT_MAP.values())))
        self.pl_target_key.setCurrentText("3B")
        simple_zone_layout.addWidget(self.pl_target_key)
        
        layout.addLayout(simple_zone_layout)
        
        # BPM filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Min BPM:"))
        self.pl_bpm_min = QSpinBox()
        self.pl_bpm_min.setMinimum(0)
        self.pl_bpm_min.setMaximum(300)
        filter_layout.addWidget(self.pl_bpm_min)
        
        filter_layout.addWidget(QLabel("Max BPM:"))
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
        create_btn = QPushButton("Create Playlist")
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
        
        clear_btn = QPushButton("Clear")
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
        title = QLabel("Check Key Compatibility")
        title_font = QFont("Segoe UI", 14, QFont.Bold)
        title.setFont(title_font)
        title.setStyleSheet("color: #1DB954;")
        layout.addWidget(title)
        
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
        check_btn = QPushButton("Check Compatibility")
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
        
        clear_btn = QPushButton("Clear")
        clear_btn.setMaximumWidth(100)
        clear_btn.clicked.connect(lambda: self.compat_output.clear())
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Output
        layout.addWidget(QLabel("Compatible Keys:"))
        self.compat_output = QTextEdit()
        self.compat_output.setReadOnly(True)
        self.compat_output.setMinimumHeight(300)
        layout.addWidget(self.compat_output)
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_about_tab(self):
        """Cria aba Sobre"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)
        
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setStyleSheet("""
            QTextEdit {
                background: white;
                border: 3px solid #1DB954;
                border-radius: 8px;
                padding: 15px;
                font-size: 11px;
            }
        """)
        about_text.setText("""
CAMEL-HOT - Harmonic Music Analyzer v2.0

═════════════════════════════════════════════════════════════

What is this?
━━━━━━━━━━━━━
An application that analyzes your music and organizes it by musical key,
facilitating professional harmonic mixing like DJs do.

Key Features:
━━━━━━━━━━━━━━━
✓ Detect musical key, BPM and duration of songs
✓ Convert to Camelot notation (DJ standard)
✓ Organize your library by musical key
✓ Create harmonic mixing playlists
✓ Check key compatibility for smooth mixing

Supported Audio Formats:
━━━━━━━━━━━━━━━━━━━━━━━━━━
MP3 • WAV • FLAC • OGG • M4A • AIFF

The Camelot Wheel System:
━━━━━━━━━━━━━━━━━━━━━━━━━━
• Numbers 1-12: The 12 musical notes (like a clock)
• A: Minor key (sad, dark sound)
• B: Major key (happy, bright sound)
• Close keys on the wheel harmonize beautifully!

Example: 8A is compatible with 7A, 8A, 9A, and 8B

DJ Tips:
━━━━━━━━━━
Harmonic mixing means playing songs that sound good together.
Use keys on the Camelot wheel to create smooth transitions!

═════════════════════════════════════════════════════════════

Made for DJs and music lovers!
Stay professional. Keep mixing. Enjoy the music!
        """)
        layout.addWidget(about_text)
        
        widget.setLayout(layout)
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
            
            # Build output with confidence bar
            output = f"🔄 Análise #{self.analyze_output.toPlainText().count('Arquivo:') + 1}\n"
            output += "═" * 60 + "\n\n"
            output += f"📀 Arquivo:     {os.path.basename(self.selected_file)}\n"
            output += f"🎵 Tonalidade:  {result.get('key', 'Desconhecido')}\n"
            output += f"🎼 Camelot:     {result.get('camelot', 'Desconhecido')}\n"
            output += f"⏱️  BPM:         {result.get('bpm', 'Desconhecido')}\n"
            output += f"⏰ Duração:     {result.get('duration', 'Desconhecida')} segundos\n"
            output += "\n"
            output += f"📊 Confiança da Análise:\n"
            output += f"   [{bar}] {confidence_pct}%\n"
            output += "\n✅ Análise concluída com sucesso!\n"
            output += "═" * 60 + "\n\n"
            
            # Get current text and append new result
            current_text = self.analyze_output.toPlainText()
            if current_text.strip():
                # If there are already results, append with separator
                self.analyze_output.setText(current_text + output)
            else:
                # First analysis
                self.analyze_output.setText(output)
            
            # Scroll to the bottom to see latest result
            self.analyze_output.verticalScrollBar().setValue(
                self.analyze_output.verticalScrollBar().maximum()
            )
            
            self.analysis_results = result
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao analisar:\n{str(e)}")
    
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


def main():
    """Função principal"""
    app = QApplication(sys.argv)
    window = DJAnalyzerGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

