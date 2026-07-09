#!/bin/bash
# DJ Harmonic Analyzer — Installer & Launcher (macOS)
# Double-click this file in Finder to open the graphical installer.
#
# GATEKEEPER NOTE: If macOS blocks this file, run once in Terminal:
#   xattr -d com.apple.quarantine "$(dirname "$0")/Install_and_Run.command"
# Or right-click the file in Finder → Open → Open (confirm the dialog).

set -euo pipefail

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

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
    echo ""
    echo " Por favor instala Python em: https://www.python.org/downloads/"
    echo ""
    osascript -e 'display alert "Python não encontrado" message "Instala Python 3.8+ em python.org antes de continuar." as critical' 2>/dev/null || true
    open "https://www.python.org/downloads/"
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
        osascript -e 'display alert "Erro de instalação" message "Falha ao instalar PyQt5. Verifica a tua ligação à internet." as critical' 2>/dev/null || true
        exit 1
    fi
fi

# ---- macOS audio stack ------------------------------------------------------
# imageio-ffmpeg ships a static ffmpeg binary — required for MP3/AAC/OGG
echo " A verificar imageio-ffmpeg (necessário para MP3/AAC)..."
if ! "$PYTHON" -c "import imageio_ffmpeg" 2>/dev/null; then
    echo " Instalando imageio-ffmpeg..."
    "$PYTHON" -m pip install "imageio-ffmpeg>=0.5.0" --quiet
    if [ $? -ne 0 ]; then
        echo " [AVISO] Falha ao instalar imageio-ffmpeg."
        echo " Análise de ficheiros MP3/AAC pode não funcionar."
    fi
fi

# ---- Remover quarentena do Gatekeeper (se necessário) -----------------------
echo " A verificar Gatekeeper..."
if xattr "$APP_DIR/installer.py" 2>/dev/null | grep -q "com.apple.quarantine"; then
    echo " Removendo atributo de quarentena..."
    xattr -dr com.apple.quarantine "$APP_DIR" 2>/dev/null || true
fi

# ---- Lançar installer GUI ---------------------------------------------------
echo " Abrindo instalador..."
echo ""
exec "$PYTHON" "$APP_DIR/installer.py"

