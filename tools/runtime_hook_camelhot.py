# Runtime hook for CAMEL-HOT frozen executable (PyInstaller)
# Executed BEFORE any user code. Fixes DLL search paths and audio codec setup.

import os
import sys
import glob

# librosa relies on Numba-dispatched functions at runtime.  Disabling JIT turns
# those dispatchers into regular functions and breaks audio loading in frozen builds.
os.environ.setdefault('NUMBA_DISABLE_CUDA', '1')
os.environ.setdefault(
    'NUMBA_CACHE_DIR',
    os.path.join(os.path.expanduser('~'), '.camelhot_numba_cache')
)

if getattr(sys, 'frozen', False):
    _bundle = sys._MEIPASS

    # -------------------------------------------------------------------------
    # CRITICAL (Windows, Python 3.8+): register ALL bundle directories in the
    # DLL search path.  Without this, _soundfile.pyd cannot find
    # libsndfile64bit.dll even though both live inside _MEIPASS.
    # os.add_dll_directory() is the official fix; we also patch PATH as a
    # fallback for older runtimes / edge cases.
    # -------------------------------------------------------------------------
    if sys.platform == 'win32':
        _dll_dirs = {_bundle}
        # Also register _soundfile_data/ sub-directory (soundfile >= 0.12)
        _sf_data = os.path.join(_bundle, '_soundfile_data')
        if os.path.isdir(_sf_data):
            _dll_dirs.add(_sf_data)
        # Scan one level deep for any sub-dirs containing DLLs
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
    # macOS: fix dynamic library loading for bundled .dylib files
    # -------------------------------------------------------------------------
    elif sys.platform == 'darwin':
        _dylib_dirs = [_bundle]
        try:
            for _name in os.listdir(_bundle):
                _sub = os.path.join(_bundle, _name)
                if os.path.isdir(_sub):
                    _dylib_dirs.append(_sub)
        except OSError:
            pass
        _dylib_path = ':'.join(_dylib_dirs)
        os.environ['DYLD_LIBRARY_PATH'] = (
            _dylib_path + ':' + os.environ.get('DYLD_LIBRARY_PATH', '')
        ).rstrip(':')

    # -------------------------------------------------------------------------
    # MP3 / AAC / OGG support via imageio_ffmpeg bundled binary.
    # audioread.ffdec uses FFMPEG_BINARY env var or PATH to locate ffmpeg.
    # This is the ONLY reliable MP3 decoder in frozen builds (audioread 3.x
    # removed the gstreamer, win_wma, and maddec backends).
    # -------------------------------------------------------------------------
    _ffmpeg_found = False
    try:
        import imageio_ffmpeg as _iff
        _ff = _iff.get_ffmpeg_exe()
        _ffd = os.path.dirname(_ff)
        os.environ['PATH'] = _ffd + os.pathsep + os.environ.get('PATH', '')
        os.environ['FFMPEG_BINARY'] = _ff
        _ffmpeg_found = True
    except Exception:
        pass

    if not _ffmpeg_found:
        # Exhaustive search for bundled ffmpeg binary
        _ffmpeg_search_dirs = [
            os.path.join(_bundle, 'imageio_ffmpeg', 'binaries'),
            os.path.join(_bundle, 'imageio_ffmpeg'),
            _bundle,
        ]
        # Also try any sub-directory that starts with "imageio"
        try:
            for _dn in os.listdir(_bundle):
                if _dn.startswith('imageio'):
                    _ffmpeg_search_dirs.insert(0, os.path.join(_bundle, _dn, 'binaries'))
                    _ffmpeg_search_dirs.insert(0, os.path.join(_bundle, _dn))
        except OSError:
            pass

        for _search in _ffmpeg_search_dirs:
            if not os.path.isdir(_search):
                continue
            try:
                for _f in os.listdir(_search):
                    _fl = _f.lower()
                    if _fl.startswith('ffmpeg') and (
                        _fl.endswith('.exe') or '.' not in _f
                    ):
                        _fp = os.path.join(_search, _f)
                        os.environ['PATH'] = _search + os.pathsep + os.environ.get('PATH', '')
                        os.environ.setdefault('FFMPEG_BINARY', _fp)
                        _ffmpeg_found = True
                        break
            except OSError:
                pass
            if _ffmpeg_found:
                break
