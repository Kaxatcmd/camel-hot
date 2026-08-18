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
# Collect Python packages with native extensions and data files explicitly.
# PyInstaller's automatic analysis can miss lazy imports and native libraries
# from the librosa/numba stack, especially on Windows and macOS.
# ---------------------------------------------------------------------------
from PyInstaller.utils.hooks import collect_all, collect_data_files

_critical_packages = (
    'librosa', 'numpy', 'scipy', 'numba', 'llvmlite', 'sklearn',
    'soundfile', 'audioread', 'imageio_ffmpeg', 'matplotlib', 'PyQt5',
)
_critical_datas = []
_critical_binaries = []
_critical_hiddenimports = []
for _package in _critical_packages:
    try:
        _datas, _binaries, _hiddenimports = collect_all(_package)
    except Exception as _collection_exc:
        print(f"ERROR: Could not collect required package '{_package}': {_collection_exc}")
        raise
    _critical_datas.extend(_datas)
    _critical_binaries.extend(_binaries)
    _critical_hiddenimports.extend(_hiddenimports)

# Backward-compatible aliases used by the existing build configuration.
_sf_datas = _sf_binaries = _sf_hiddenimports = []

# imageio-ffmpeg: ships a static ffmpeg binary — needed for MP3/AAC/m4a decoding
try:
    import importlib.util as _ilu
    if _ilu.find_spec('imageio_ffmpeg') is None:
        raise ImportError("imageio_ffmpeg not installed")
    _iff_datas, _iff_binaries, _iff_hiddenimports = [], [], []
except Exception as _iff_exc:
    print(f"ERROR: imageio_ffmpeg collection failed: {_iff_exc}")
    print("ERROR: MP3/AAC decoding WILL BE BROKEN in the frozen bundle.")
    print("SOLUTION: Install imageio-ffmpeg before building:")
    print("  pip install imageio-ffmpeg")
    print("  Then rebuild.")
    import sys as _sys
    _sys.exit(1)  # Fail fast — do not silently produce a broken build

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
] + _critical_datas + _lr_datas

# Windows-specific: explicitly bundle libsndfile64bit.dll inside _soundfile_data/
# collect_all('soundfile') should already include this, but we add it explicitly
# to guarantee the DLL lands in the correct sub-directory of the frozen bundle.
if sys.platform == "win32":
    try:
        import soundfile as _sf_mod
        _sf_data_dir = Path(_sf_mod.__file__).parent / "_soundfile_data"
        _libsndfile_dll = _sf_data_dir / "libsndfile64bit.dll"
        if _libsndfile_dll.exists():
            added_datas.append((str(_libsndfile_dll), "_soundfile_data"))
        else:
            print("WARNING: libsndfile64bit.dll not found — soundfile may not work in the bundle.")
    except Exception as _dll_exc:
        print(f"WARNING: Could not locate libsndfile64bit.dll: {_dll_exc}")

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
    "audioread.rawread",   # raw/soundfile backend (WAV, FLAC, etc.)
    "audioread.ffdec",    # ffmpeg backend — primary MP3/AAC decoder
    # NOTE: audioread.gstreamer, audioread.win_wma, audioread.maddec were
    # removed from audioread 3.x — do NOT add them as hidden imports.
    "imageio_ffmpeg",     # provides the static ffmpeg binary used by audioread.ffdec
    # matplotlib
    "matplotlib",
    "matplotlib.backends.backend_qt5agg",
    "matplotlib.backends.backend_agg",
    # PyQt5 extras used by the app
    "PyQt5.QtSvg",
    "PyQt5.QtPrintSupport",
] + _critical_hiddenimports

# ---------------------------------------------------------------------------
# Modules to exclude (reduces bundle size — only safe exclusions)
# ---------------------------------------------------------------------------
# WARNING: Do NOT exclude urllib, http, html, email, xml — librosa and
# several other dependencies import them internally at runtime.
# NOTE: numba and llvmlite are optional librosa accelerators. They are NOT
# excluded here because doing so can break the librosa import chain on some
# Windows environments (numba hooks alter how llvmlite DLLs are resolved).
excludes = [
    "tkinter",   # safe — never used by audio stack
]

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
a = Analysis(
    ["main.py"],
    pathex=[str(SPEC_DIR)],
    binaries=vlc_binaries + _critical_binaries,
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
    console=False,       # Windowed app — no console window in production
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
            "CFBundleShortVersionString": "2.1",
            "CFBundleVersion": "2.1.1",
            "NSHighResolutionCapable": True,
            # 10.15 (Catalina) minimum — first macOS with notarization enforcement.
            # Older targets risk linking against removed APIs.
            "LSMinimumSystemVersion": "10.15.0",
            "NSHumanReadableCopyright": "\u00a9 2024 Kaxatcmd",
            # Required on Ventura/Sonoma for microphone/file access dialogs
            "NSAppleEventsUsageDescription": "CamelHot needs file access to analyze audio.",
        },
    )
