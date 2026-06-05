# Runtime hook for CAMEL-HOT frozen executable (PyInstaller)
# This file is executed BEFORE any user code when the app starts.
# It patches the environment so librosa works correctly inside a frozen bundle.

import os

# Disable numba JIT compilation — prevents llvmlite/LLVM native-lib failures.
# librosa works perfectly without JIT; numba is only an optional accelerator.
os.environ.setdefault('NUMBA_DISABLE_JIT', '1')

# Keep numba cache out of the read-only _internal/ bundle directory.
os.environ.setdefault(
    'NUMBA_CACHE_DIR',
    os.path.join(os.path.expanduser('~'), '.camelhot_numba_cache')
)
