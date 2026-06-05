#!/usr/bin/env bash
# =============================================================
#  CAMEL-HOT — Utilitário: Copiar libs VLC (Linux)
#  Uso: bash build_linux/get_vlc_libs.sh
# =============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${PROJECT_ROOT}/vlc_libs"

echo "============================================================"
echo "  CAMEL-HOT — Utilitário: Copiar libs VLC (Linux)"
echo "============================================================"
echo ""
echo "  Copia libvlc.so, libvlccore.so e plugins/ para vlc_libs/"
echo "  para serem incluídas no build do PyInstaller."
echo ""

# ---------------------------------------------------------------------------
# Step 1 — Ensure VLC is installed
# ---------------------------------------------------------------------------
echo "[1/2] A verificar VLC instalado..."

if ! ldconfig -p 2>/dev/null | grep -q "libvlc.so"; then
    echo "    libvlc não encontrada no sistema."
    echo "    A instalar VLC e libvlc-dev..."
    sudo apt-get update -qq
    sudo apt-get install -y vlc libvlc-dev
fi

# Locate the canonical .so paths (follow symlinks so we get the real file)
VLC_SO=$(find \
    /usr/lib /usr/lib/x86_64-linux-gnu /usr/local/lib \
    -name "libvlc.so*" -not -name "libvlccore*" 2>/dev/null | sort | head -1 || true)

VLC_CORE_SO=$(find \
    /usr/lib /usr/lib/x86_64-linux-gnu /usr/local/lib \
    -name "libvlccore.so*" 2>/dev/null | sort | head -1 || true)

if [ -z "${VLC_SO}" ]; then
    echo "    ERRO: libvlc.so não encontrada."
    echo "    Instala manualmente: sudo apt-get install vlc libvlc-dev"
    exit 1
fi

echo "    libvlc     : ${VLC_SO}"
[ -n "${VLC_CORE_SO}" ] && echo "    libvlccore : ${VLC_CORE_SO}"
echo ""

# ---------------------------------------------------------------------------
# Step 2 — Copy libs
# ---------------------------------------------------------------------------
echo "[2/2] A copiar libs para vlc_libs/..."
mkdir -p "${TARGET_DIR}"

cp -v "$(readlink -f "${VLC_SO}")" "${TARGET_DIR}/"
if [ -n "${VLC_CORE_SO}" ]; then
    cp -v "$(readlink -f "${VLC_CORE_SO}")" "${TARGET_DIR}/"
fi

# Also copy the .so symlinks so runtime linker resolves them correctly
for _link in "${VLC_SO}" "${VLC_CORE_SO}"; do
    [ -L "${_link}" ] && cp -vP "${_link}" "${TARGET_DIR}/" 2>/dev/null || true
done

# Plugins folder — search common locations
VLC_PLUGIN_FOUND=false
for _pdir in \
    "/usr/lib/x86_64-linux-gnu/vlc/plugins" \
    "/usr/lib/vlc/plugins" \
    "/usr/local/lib/vlc/plugins"; do
    if [ -d "${_pdir}" ]; then
        echo "    A copiar plugins de ${_pdir} ..."
        rm -rf "${TARGET_DIR}/plugins"
        cp -r "${_pdir}" "${TARGET_DIR}/plugins"
        VLC_PLUGIN_FOUND=true
        break
    fi
done

if ! ${VLC_PLUGIN_FOUND}; then
    echo "    AVISO: Pasta de plugins VLC não encontrada."
    echo "    A reprodução de áudio pode não funcionar corretamente."
fi

echo ""
echo "============================================================"
echo "  VLC libs copiadas para vlc_libs/ — pronto para build!"
echo ""
echo "  Ficheiros:"
ls -lh "${TARGET_DIR}"/*.so* 2>/dev/null || true
[ -d "${TARGET_DIR}/plugins" ] && echo "  vlc_libs/plugins/  ($(ls "${TARGET_DIR}/plugins" | wc -l) entradas)"
echo ""
echo "  Passo seguinte: bash build_linux/build.sh"
echo "============================================================"
