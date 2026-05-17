#!/usr/bin/env bash
# =============================================================
#  CAMEL-HOT — macOS Build Script
#  Gera: dist/CamelHot.dmg
#  Uso:  bash build_macos/build.sh
# =============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

echo "============================================================"
echo "  CAMEL-HOT — macOS Build Script"
echo "============================================================"
echo ""

# ---------------------------------------------------------------------------
# Step 1 — Verify / install PyInstaller
# ---------------------------------------------------------------------------
echo "[1/5] Verificando PyInstaller..."
if ! command -v pyinstaller &>/dev/null; then
    echo "    PyInstaller não encontrado. A instalar..."
    pip install pyinstaller
    echo "    PyInstaller instalado com sucesso."
else
    echo "    Versão: $(pyinstaller --version)"
fi
echo ""

# ---------------------------------------------------------------------------
# Step 2 — Verify create-dmg
# ---------------------------------------------------------------------------
echo "[2/5] Verificando create-dmg..."
if ! command -v create-dmg &>/dev/null; then
    echo "    create-dmg não encontrado."
    echo ""
    echo "    Para instalar via Homebrew:"
    echo "      brew install create-dmg"
    echo ""
    read -r -p "    Instalar agora via brew? [s/N] " choice
    case "${choice}" in
        s|S|y|Y)
            if command -v brew &>/dev/null; then
                brew install create-dmg
            else
                echo "    ERRO: Homebrew não encontrado. Instala em https://brew.sh"
                exit 1
            fi
            ;;
        *)
            echo "    AVISO: O .dmg não será criado sem create-dmg."
            echo "    O build do PyInstaller ficará em dist/CamelHot.app"
            CREATE_DMG_AVAILABLE=false
            ;;
    esac
else
    echo "    create-dmg encontrado: $(create-dmg --version 2>/dev/null || echo 'ok')"
    CREATE_DMG_AVAILABLE=true
fi
echo ""

# ---------------------------------------------------------------------------
# Step 3 — Clean previous dist/
# ---------------------------------------------------------------------------
echo "[3/5] A limpar builds anteriores..."
if [ -d "dist/CamelHot.app" ]; then
    rm -rf "dist/CamelHot.app"
    echo "    dist/CamelHot.app removido."
fi
if [ -f "dist/CamelHot.dmg" ]; then
    rm -f "dist/CamelHot.dmg"
    echo "    dist/CamelHot.dmg removido."
fi
echo ""

# ---------------------------------------------------------------------------
# Step 4 — Run PyInstaller
# ---------------------------------------------------------------------------
echo "[4/5] A correr PyInstaller..."
pyinstaller camel_hot.spec --clean --noconfirm

if [ ! -d "dist/CamelHot.app" ]; then
    echo ""
    echo "    ERRO: dist/CamelHot.app não foi criado."
    echo "    Consulta o output do PyInstaller acima."
    exit 1
fi
echo "    OK — dist/CamelHot.app criado."
echo ""

# ---------------------------------------------------------------------------
# Step 5 — Create .dmg
# ---------------------------------------------------------------------------
echo "[5/5] A criar imagem de disco .dmg..."

if [ "${CREATE_DMG_AVAILABLE:-true}" = "false" ]; then
    echo "    A saltar criação do .dmg (create-dmg não disponível)."
    echo ""
    echo "============================================================"
    echo "  Build concluído (sem .dmg)."
    echo "  App em: dist/CamelHot.app"
    echo "============================================================"
    exit 0
fi

# Ícone do volume (opcional)
VOLICON_ARGS=()
if [ -f "assets/camel_hot.icns" ]; then
    VOLICON_ARGS=(--volicon "assets/camel_hot.icns")
fi

create-dmg \
    --volname "CAMEL-HOT" \
    "${VOLICON_ARGS[@]}" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "CamelHot.app" 150 185 \
    --hide-extension "CamelHot.app" \
    --app-drop-link 450 185 \
    "dist/CamelHot.dmg" \
    "dist/CamelHot.app"

if [ ! -f "dist/CamelHot.dmg" ]; then
    echo "    ERRO: dist/CamelHot.dmg não foi criado."
    exit 1
fi

DMG_SIZE=$(du -sh "dist/CamelHot.dmg" | cut -f1)

echo ""
echo "============================================================"
echo "  Build concluído com sucesso!"
echo "  Ficheiro: dist/CamelHot.dmg"
echo "  Tamanho:  ${DMG_SIZE}"
echo "============================================================"
