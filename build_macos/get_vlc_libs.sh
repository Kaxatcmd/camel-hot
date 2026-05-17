#!/usr/bin/env bash
# =============================================================
#  CAMEL-HOT — Utilitário: Copiar libs VLC (macOS)
#  Uso: bash build_macos/get_vlc_libs.sh
# =============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${PROJECT_ROOT}/vlc_libs"

echo "============================================================"
echo "  CAMEL-HOT — Utilitário: Copiar libs VLC (macOS)"
echo "============================================================"
echo ""
echo "  Este script copia as bibliotecas nativas do VLC para"
echo "  vlc_libs/ para serem incluídas no build do PyInstaller."
echo ""

# ---------------------------------------------------------------------------
# Procurar VLC
# ---------------------------------------------------------------------------
echo "[1/2] A procurar VLC instalado..."

VLC_LIB_PATHS=(
    "/Applications/VLC.app/Contents/MacOS/lib"
)

VLC_DIR=""
for _path in "${VLC_LIB_PATHS[@]}"; do
    if [ -f "${_path}/libvlc.dylib" ]; then
        echo "    VLC encontrado em: ${_path}"
        VLC_DIR="${_path}"
        break
    fi
done

if [ -z "${VLC_DIR}" ]; then
    echo "    VLC não encontrado."
    echo ""
    echo "    Para instalar o VLC:"
    echo "      brew install --cask vlc"
    echo "    ou descarregar em:"
    echo "      https://www.videolan.org/vlc/download-macosx.html"
    echo ""
    exit 1
fi
echo ""

# ---------------------------------------------------------------------------
# Copiar libs para vlc_libs/
# ---------------------------------------------------------------------------
echo "[2/2] A copiar libs para vlc_libs/..."

mkdir -p "${TARGET_DIR}"

echo "    A copiar libvlc.dylib..."
cp -f "${VLC_DIR}/libvlc.dylib" "${TARGET_DIR}/"

echo "    A copiar libvlccore.dylib..."
cp -f "${VLC_DIR}/libvlccore.dylib" "${TARGET_DIR}/"

# Pasta plugins (no .app está um nível acima de /lib)
VLC_PLUGINS_DIR="$(dirname "${VLC_DIR}")/plugins"
if [ -d "${VLC_PLUGINS_DIR}" ]; then
    echo "    A copiar pasta plugins/ (pode demorar alguns segundos)..."
    rm -rf "${TARGET_DIR}/plugins"
    cp -r "${VLC_PLUGINS_DIR}" "${TARGET_DIR}/plugins"
    echo "    Pasta plugins copiada."
else
    echo "    AVISO: Pasta plugins não encontrada em ${VLC_PLUGINS_DIR}"
    echo "    A reprodução de áudio pode não funcionar corretamente."
fi

echo ""
echo "============================================================"
echo "  VLC libs copiadas para vlc_libs/ — pronto para build!"
echo ""
echo "  Ficheiros copiados:"
echo "    vlc_libs/libvlc.dylib"
echo "    vlc_libs/libvlccore.dylib"
echo "    vlc_libs/plugins/  (pasta completa)"
echo ""
echo "  Passo seguinte: bash build_macos/build.sh"
echo "============================================================"
