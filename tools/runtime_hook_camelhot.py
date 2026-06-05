# Runtime hook for CAMEL-HOT frozen executable (PyInstaller)
# This file is executed BEFORE any user code when the app starts.
# It patches the environment so librosa works correctly inside a frozen bundle.

import os
import sys

# Disable numba JIT compilation — prevents llvmlite/LLVM native-lib failures.
# librosa works perfectly without JIT; numba is only an optional accelerator.
os.environ.setdefault('NUMBA_DISABLE_JIT', '1')

# Keep numba cache out of the read-only _internal/ bundle directory.
os.environ.setdefault(
    'NUMBA_CACHE_DIR',
    os.path.join(os.path.expanduser('~'), '.camelhot_numba_cache')
)

# ---------------------------------------------------------------------------
# MP3 / AAC / m4a support — locate the bundled imageio-ffmpeg binary and
# add its directory to PATH so that audioread (used by librosa) can find it.
# ---------------------------------------------------------------------------
if getattr(sys, 'frozen', False):
    _bundle = sys._MEIPASS
    # imageio-ffmpeg writes its binary to a sub-path inside the package dir.
    # collect_all('imageio_ffmpeg') puts it at _MEIPASS/imageio_ffmpeg/
    _candidates = [
        os.path.join(_bundle, 'imageio_ffmpeg', 'binaries'),
        os.path.join(_bundle, 'imageio_ffmpeg'),
        _bundle,
    ]
    for _d in _candidates:
        if os.path.isdir(_d):
            _exes = [f for f in os.listdir(_d)
                     if f.lower().startswith('ffmpeg') and
                     (f.lower().endswith('.exe') or '.' not in f)]
            if _exes:
                os.environ['PATH'] = _d + os.pathsep + os.environ.get('PATH', '')
                # Also set FFMPEG_BINARY for pydub/audioread compatibility
                os.environ.setdefault('FFMPEG_BINARY', os.path.join(_d, _exes[0]))
                break
