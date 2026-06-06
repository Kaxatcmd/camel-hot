# -*- mode: python ; coding: utf-8 -*-
#
# camel_hot.spec — PyInstaller build specification for CAMEL-HOT
#
# Usage:
#   pyinstaller camel_hot.spec --clean --noconfirm
#
# Do NOT edit paths below; adjust via the build scripts in build_windows/ or build_macos/.

import sys
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# Collect soundfile native libs (libsndfile DLL/SO) and librosa data files.
# These are not auto-detected by PyInstaller but are required at runtime.
# ---------------------------------------------------------------------------
from PyInstaller.utils.hooks import collect_all, collect_data_files

# soundfile: gets _soundfile.pyd + libsndfile64bit.dll (Windows) or .so (Linux/macOS)
_sf_datas, _sf_binaries, _sf_hiddenimports = collect_all('soundfile')

# imageio-ffmpeg: ships a static ffmpeg binary — needed for MP3/AAC/m4a decoding
try:
    _iff_datas, _iff_binaries, _iff_hiddenimports = collect_all('imageio_ffmpeg')
except Exception:
    _iff_datas, _iff_binaries, _iff_hiddenimports = [], [], []

# librosa: bundled filter/data files (mel filterbanks, etc.)
try:
    _lr_datas = collect_data_files('librosa', include_py_files=False)
except Exception:
    _lr_datas = []

# ---------------------------------------------------------------------------
# Resolve project root (directory containing this .spec file)
# ---------------------------------------------------------------------------
SPEC_DIR = Path(SPECPATH)  # PyInstaller sets SPECPATH at runtime

# ---------------------------------------------------------------------------
# Icon — use platform-specific icon if it exists, otherwise no icon
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    _icon_candidate = SPEC_DIR / "assets" / "camel_hot.ico"
    icon = str(_icon_candidate) if _icon_candidate.exists() else None
elif sys.platform == "darwin":
    _icon_candidate = SPEC_DIR / "assets" / "camel_hot.icns"
    icon = str(_icon_candidate) if _icon_candidate.exists() else None
else:
    # Linux: PyInstaller does not embed icons in ELF binaries.
    # The 512-px PNG is referenced by camel_hot.desktop inside the AppImage.
    icon = None

# ---------------------------------------------------------------------------
# VLC native libraries — bundled only when available
# ---------------------------------------------------------------------------
vlc_binaries = []

if sys.platform == "win32":
    _vlc_search_paths = [
        SPEC_DIR / "vlc_libs",
        Path("C:/Program Files/VideoLAN/VLC"),
        Path("C:/Program Files (x86)/VideoLAN/VLC"),
    ]
    for _vlc_dir in _vlc_search_paths:
        _libvlc = _vlc_dir / "libvlc.dll"
        _libvlccore = _vlc_dir / "libvlccore.dll"
        if _libvlc.exists() and _libvlccore.exists():
            vlc_binaries.append((str(_libvlc), "."))
            vlc_binaries.append((str(_libvlccore), "."))
            # Include plugins folder if present
            _plugins = _vlc_dir / "plugins"
            if _plugins.exists():
                vlc_binaries.append((str(_plugins / "*"), "plugins"))
            break

elif sys.platform == "darwin":
    _vlc_search_paths = [
        SPEC_DIR / "vlc_libs",
        Path("/Applications/VLC.app/Contents/MacOS/lib"),
    ]
    for _vlc_dir in _vlc_search_paths:
        _libvlc = _vlc_dir / "libvlc.dylib"
        _libvlccore = _vlc_dir / "libvlccore.dylib"
        if _libvlc.exists() and _libvlccore.exists():
            vlc_binaries.append((str(_libvlc), "."))
            vlc_binaries.append((str(_libvlccore), "."))
            _plugins = _vlc_dir.parent / "plugins"
            if _plugins.exists():
                vlc_binaries.append((str(_plugins / "*"), "plugins"))
            break

elif sys.platform.startswith("linux"):
    # Linux: use pre-copied libs from vlc_libs/ (run build_linux/get_vlc_libs.sh first)
    _vlc_dir = SPEC_DIR / "vlc_libs"
    if _vlc_dir.exists():
        for _so in _vlc_dir.glob("*.so*"):
            vlc_binaries.append((str(_so), "."))
        _plugins = _vlc_dir / "plugins"
        if _plugins.exists():
            vlc_binaries.append((str(_plugins / "*"), "plugins"))

# ---------------------------------------------------------------------------
# Data files to bundle
# ---------------------------------------------------------------------------
added_datas = [
    ("assets/", "assets"),
    ("gui/", "gui"),
    ("utils/", "utils"),
    ("audio_analysis/", "audio_analysis"),
    ("config.py", "."),
    ("logging_config.py", "."),
] + _sf_datas + _lr_datas + _iff_datas

# Linux: include .desktop and 512-px icon for system integration
if sys.platform.startswith("linux"):
    _desktop = SPEC_DIR / "assets" / "camel_hot.desktop"
    _icon512 = SPEC_DIR / "assets" / "camel_hot_512.png"
    if _desktop.exists():
        added_datas.append((str(_desktop), "assets"))
    if _icon512.exists():
        added_datas.append((str(_icon512), "assets"))

# ---------------------------------------------------------------------------
# Hidden imports required by librosa, sklearn, scipy, matplotlib, and PyQt5
# ---------------------------------------------------------------------------
hidden_imports = [
    # librosa core
    "librosa",
    "librosa.core",
    "librosa.core.audio",
    "librosa.core.constantq",
    "librosa.core.convert",
    "librosa.core.fft",
    "librosa.core.pitch",
    "librosa.core.spectrum",
    "librosa.core.time_frequency",
    "librosa.feature",
    "librosa.feature.spectral",
    "librosa.feature.rhythm",
    "librosa.util",
    "librosa.util.utils",
    "librosa.filters",
    "librosa.effects",
    "librosa.beat",
    "librosa.onset",
    # scikit-learn
    "sklearn",
    "sklearn.utils",
    "sklearn.utils._cython_blas",
    "sklearn.utils._weight_vector",
    "sklearn.neighbors",
    "sklearn.neighbors.typedefs",
    "sklearn.neighbors._partition_nodes",
    "sklearn.neighbors._ball_tree",
    "sklearn.neighbors._kd_tree",
    "sklearn.preprocessing",
    # scipy
    "scipy._lib.messagestream",
    "scipy.signal",
    "scipy.signal.windows",
    "scipy.fft",
    "scipy.special._ufuncs",
    # audio I/O
    "soundfile",
    "soundfile._soundfile",
    "cffi",
    "audioread",
    "audioread.rawread",
    "audioread.gstreamer",
    "audioread.ffdec",
    "audioread.maddec",
    "audioread.win_wma",   # Windows Media Foundation backend (MP3 on Windows)
    "imageio_ffmpeg",
    # matplotlib
    "matplotlib",
    "matplotlib.backends.backend_qt5agg",
    "matplotlib.backends.backend_agg",
    # PyQt5 extras used by the app
    "PyQt5.QtSvg",
    "PyQt5.QtPrintSupport",
] + _sf_hiddenimports + _iff_hiddenimports

# ---------------------------------------------------------------------------
# Modules to exclude (reduces bundle size — only safe exclusions)
# ---------------------------------------------------------------------------
# WARNING: Do NOT exclude urllib, http, html, email, xml — librosa and
# several other dependencies import them internally at runtime.
excludes = [
    "tkinter",   # only truly safe exclusion — never imported by audio stack
]

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(
    ["main.py"],
    pathex=[str(SPEC_DIR)],
    binaries=vlc_binaries + _sf_binaries + _iff_binaries,
    datas=added_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["tools/runtime_hook_camelhot.py"],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CamelHot",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,       # windowed — no terminal visible
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="CamelHot",
)

# ---------------------------------------------------------------------------
# macOS .app bundle
# ---------------------------------------------------------------------------
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="CamelHot.app",
        icon=icon,
        bundle_identifier="com.kaxatcmd.camelhot",
        info_plist={
            "CFBundleShortVersionString": "2.0",
            "CFBundleVersion": "2.0.0",
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "10.13.0",
            "NSHumanReadableCopyright": "© 2024 Kaxatcmd",
        },
    )
