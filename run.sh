#!/bin/bash
# DJ Harmonic Analyzer — Installer & Launcher (Linux)
# Abre o instalador gráfico PyQt5.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo " ====================================================="
echo "  DJ Harmonic Analyzer"
echo " ====================================================="
echo ""

# ---- Verificar Python -------------------------------------------------------
PYTHON=""
for candidate in python3 python3.12 python3.11 python3.10 python3.9 python3.8 python; do
    if command -v "$candidate" &>/dev/null; then
        VER=$("$candidate" -c "import sys; print(sys.version_info >= (3,8))" 2>/dev/null)
        if [ "$VER" = "True" ]; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo " [ERRO] Python 3.8+ não encontrado."
    echo " Instala com: sudo apt install python3  (ou equivalente)"
    exit 1
fi

echo " Usando: $($PYTHON --version)"

# ---- Bootstrap PyQt5 --------------------------------------------------------
echo " A verificar PyQt5..."
if ! "$PYTHON" -c "import PyQt5" 2>/dev/null; then
    echo " Instalando PyQt5 para o instalador gráfico..."
    "$PYTHON" -m pip install "PyQt5>=5.15.0" --quiet
    if [ $? -ne 0 ]; then
        echo " [ERRO] Falha ao instalar PyQt5."
        echo " Tenta: pip install PyQt5  ou  sudo apt install python3-pyqt5"
        exit 1
    fi
fi

# ---- imageio-ffmpeg (necessário para MP3/AAC) --------------------------------
echo " A verificar imageio-ffmpeg..."
if ! "$PYTHON" -c "import imageio_ffmpeg" 2>/dev/null; then
    echo " Instalando imageio-ffmpeg..."
    "$PYTHON" -m pip install "imageio-ffmpeg>=0.5.0" --quiet || \
        echo " [AVISO] Falha ao instalar imageio-ffmpeg. Análise de MP3/AAC pode falhar."
fi

# ---- Lançar installer GUI ---------------------------------------------------
echo " Abrindo instalador..."
echo ""
exec "$PYTHON" "$SCRIPT_DIR/installer.py"

