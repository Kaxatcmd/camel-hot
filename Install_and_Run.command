#!/bin/bash
# DJ Harmonic Analyzer — Installer & Launcher (macOS)
# Double-click this file in Finder to open the graphical installer.

cd "$(dirname "$0")"

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
    osascript -e 'display alert "Python não encontrado" message "Instala Python 3.8+ em python.org antes de continuar." as critical'
    open "https://www.python.org/downloads/"
    exit 1
fi

echo " Usando: $($PYTHON --version)"

# ---- Bootstrap PyQt5 --------------------------------------------------------
echo " A verificar PyQt5..."
"$PYTHON" -c "import PyQt5" 2>/dev/null
if [ $? -ne 0 ]; then
    echo " Instalando PyQt5 para o instalador gráfico..."
    "$PYTHON" -m pip install "PyQt5>=5.15.0" --quiet
    if [ $? -ne 0 ]; then
        echo " [ERRO] Falha ao instalar PyQt5."
        osascript -e 'display alert "Erro de instalação" message "Falha ao instalar PyQt5. Verifica a tua ligação à internet." as critical'
        exit 1
    fi
fi

# ---- Lançar installer GUI ---------------------------------------------------
echo " Abrindo instalador..."
echo ""
exec "$PYTHON" "$(dirname "$0")/installer.py"
