#!/usr/bin/env bash
# =============================================================
#  CAMEL-HOT — Linux Build Script
#  Output: dist/CamelHot-x86_64.AppImage
#  Usage:  bash build_linux/build.sh
# =============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

echo "============================================================"
echo "  CAMEL-HOT — Linux Build Script"
echo "============================================================"
echo ""

# ---------------------------------------------------------------------------
# Step 1 — Generate icon assets
# ---------------------------------------------------------------------------
echo "[1/6] Gerando ícones..."
python3 tools/generate_icons.py
echo ""

# ---------------------------------------------------------------------------
# Step 2 — Verify / install PyInstaller
# ---------------------------------------------------------------------------
echo "[2/6] Verificando PyInstaller..."
if ! command -v pyinstaller &>/dev/null; then
    echo "    PyInstaller não encontrado. A instalar..."
    pip3 install pyinstaller
    echo "    PyInstaller instalado."
else
    echo "    Versão: $(pyinstaller --version)"
fi
echo ""

# ---------------------------------------------------------------------------
# Step 3 — Clean previous dist/
# ---------------------------------------------------------------------------
echo "[3/6] A limpar builds anteriores..."
rm -rf dist/CamelHot dist/AppDir dist/CamelHot-x86_64.AppImage
echo "    Limpo."
echo ""

# ---------------------------------------------------------------------------
# Step 4 — Run PyInstaller
# ---------------------------------------------------------------------------
echo "[4/6] A correr PyInstaller..."
pyinstaller camel_hot.spec --clean --noconfirm

if [ ! -f "dist/CamelHot/CamelHot" ]; then
    echo ""
    echo "    ERRO: dist/CamelHot/CamelHot não foi criado."
    echo "    Consulta o output do PyInstaller acima."
    exit 1
fi
echo "    OK — dist/CamelHot/ criado."
echo ""

# ---------------------------------------------------------------------------
# Step 5 — Assemble AppDir
# ---------------------------------------------------------------------------
echo "[5/6] A montar AppDir..."

APPDIR="${PROJECT_ROOT}/dist/AppDir"
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/share/icons/hicolor/512x512/apps"
mkdir -p "${APPDIR}/usr/share/applications"

# Copy entire PyInstaller output into usr/bin (preserves _internal/ layout)
cp -r dist/CamelHot/. "${APPDIR}/usr/bin/"

# .desktop and icon at AppDir root (AppImage spec requirement)
cp assets/camel_hot.desktop "${APPDIR}/CamelHot.desktop"
cp assets/camel_hot_512.png "${APPDIR}/camel_hot.png"

# Standard XDG icon/application paths (for system integration after install)
cp assets/camel_hot_512.png "${APPDIR}/usr/share/icons/hicolor/512x512/apps/camel_hot.png"
cp assets/camel_hot.desktop "${APPDIR}/usr/share/applications/CamelHot.desktop"

# AppRun launcher
cat > "${APPDIR}/AppRun" << 'APPRUN_EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=$(dirname "$SELF")
APPBIN="${HERE}/usr/bin"

# Add bundled libs and optional VLC plugins to the search paths
export LD_LIBRARY_PATH="${APPBIN}/_internal:${APPBIN}:${LD_LIBRARY_PATH:-}"
export VLC_PLUGIN_PATH="${APPBIN}/_internal/plugins:${APPBIN}/plugins:${VLC_PLUGIN_PATH:-}"

# Qt platform plugin path
export QT_QPA_PLATFORM_PLUGIN_PATH="${APPBIN}/_internal/PyQt5/Qt5/plugins/platforms:${QT_QPA_PLATFORM_PLUGIN_PATH:-}"

exec "${APPBIN}/CamelHot" "$@"
APPRUN_EOF
chmod +x "${APPDIR}/AppRun"

echo "    AppDir montado em dist/AppDir/"
echo ""

# ---------------------------------------------------------------------------
# Step 6 — Create AppImage with appimagetool
# ---------------------------------------------------------------------------
echo "[6/6] A criar AppImage..."

APPIMAGETOOL="${PROJECT_ROOT}/dist/appimagetool-x86_64.AppImage"

if [ ! -f "${APPIMAGETOOL}" ]; then
    echo "    A descarregar appimagetool..."
    curl -fsSLo "${APPIMAGETOOL}" \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "${APPIMAGETOOL}"
    echo "    appimagetool descarregado."
fi

ARCH=x86_64 "${APPIMAGETOOL}" --no-appstream \
    "${APPDIR}" "dist/CamelHot-x86_64.AppImage"

if [ ! -f "dist/CamelHot-x86_64.AppImage" ]; then
    echo "    ERRO: dist/CamelHot-x86_64.AppImage não foi criado."
    exit 1
fi

SIZE=$(du -sh "dist/CamelHot-x86_64.AppImage" | cut -f1)

echo ""
echo "============================================================"
echo "  Build concluído com sucesso!"
echo ""
echo "  Ficheiro: dist/CamelHot-x86_64.AppImage"
echo "  Tamanho:  ${SIZE}"
echo ""
echo "  Para executar:"
echo "    chmod +x dist/CamelHot-x86_64.AppImage"
echo "    ./dist/CamelHot-x86_64.AppImage"
echo "============================================================"
