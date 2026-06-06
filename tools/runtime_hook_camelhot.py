# Runtime hook for CAMEL-HOT frozen executable (PyInstaller)
# Executed BEFORE any user code. Fixes DLL search paths and audio codec setup.

import os
import sys

os.environ.setdefault('NUMBA_DISABLE_JIT', '1')
os.environ.setdefault(
    'NUMBA_CACHE_DIR',
    os.path.join(os.path.expanduser('~'), '.camelhot_numba_cache')
)

if getattr(sys, 'frozen', False):
    _bundle = sys._MEIPASS

    # -------------------------------------------------------------------------
    # CRITICAL (Windows, Python 3.8+): register bundle directories in the DLL
    # search path.  Without this, _soundfile.pyd cannot find libsndfile64bit.dll
    # even though both are inside _MEIPASS.  os.add_dll_directory() is the
    # official fix; we fall back to adding to PATH for older Python.
    # -------------------------------------------------------------------------
    if sys.platform == 'win32':
        _dll_dirs = {_bundle}
        try:
            for _name in os.listdir(_bundle):
                _sub = os.path.join(_bundle, _name)
                if os.path.isdir(_sub):
                    for _f in os.listdir(_sub):
                        if _f.lower().endswith('.dll'):
                            _dll_dirs.add(_sub)
                            break
        except OSError:
            pass

        for _d in _dll_dirs:
            try:
                os.add_dll_directory(_d)          # Python 3.8+
            except (AttributeError, OSError):
                pass
            os.environ['PATH'] = _d + os.pathsep + os.environ.get('PATH', '')

    # -------------------------------------------------------------------------
    # MP3 / AAC support: locate the bundled imageio-ffmpeg binary and expose it
    # to audioread (the fallback decoder used by librosa for non-PCM formats).
    # -------------------------------------------------------------------------
    _ffmpeg_found = False
    try:
        import imageio_ffmpeg
        _ff = imageio_ffmpeg.get_ffmpeg_exe()
        _ffd = os.path.dirname(_ff)
        os.environ['PATH'] = _ffd + os.pathsep + os.environ.get('PATH', '')
        os.environ['FFMPEG_BINARY'] = _ff
        _ffmpeg_found = True
    except Exception:
        pass

    if not _ffmpeg_found:
        for _search in [
            os.path.join(_bundle, 'imageio_ffmpeg', 'binaries'),
            os.path.join(_bundle, 'imageio_ffmpeg'),
            _bundle,
        ]:
            if not os.path.isdir(_search):
                continue
            for _f in os.listdir(_search):
                if _f.lower().startswith('ffmpeg') and (
                    _f.lower().endswith('.exe') or '.' not in _f
                ):
                    _fp = os.path.join(_search, _f)
                    os.environ['PATH'] = _search + os.pathsep + os.environ.get('PATH', '')
                    os.environ.setdefault('FFMPEG_BINARY', _fp)
                    _ffmpeg_found = True
                    break
            if _ffmpeg_found:
                break
