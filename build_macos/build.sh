#!/usr/bin/env bash
# =============================================================
#  CAMEL-HOT — macOS Build Script
#  Gera: dist/CamelHot.dmg
#  Uso:  bash build_macos/build.sh
#
#  ARQUITETURA: Por defeito gera um binário para a arquitetura
#  nativa do Mac onde o script é executado.
#  Para gerar um binário universal (Intel + Apple Silicon):
#    ARCH=universal2 bash build_macos/build.sh
# =============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${PROJECT_ROOT}"

# Arquitetura alvo (pode ser sobrescrita com ARCH=universal2)
TARGET_ARCH="${ARCH:-}"

echo "============================================================"
echo "  CAMEL-HOT — macOS Build Script"
echo "============================================================"
if [ -n "$TARGET_ARCH" ]; then
    echo "  Arquitetura alvo: $TARGET_ARCH"
else
    echo "  Arquitetura alvo: nativa ($(uname -m))"
fi
echo ""

# ---------------------------------------------------------------------------
# Step 0 — Verify critical dependencies are installed
# ---------------------------------------------------------------------------
echo "[0/6] Verificando dependências de build..."

python3 -c "import numpy, scipy, numba, llvmlite, soundfile, audioread, imageio_ffmpeg, librosa"
echo "    Runtime científico: OK"

# imageio-ffmpeg is required — abort if missing
if ! python3 -c "import imageio_ffmpeg" 2>/dev/null; then
    echo "    ERRO: imageio-ffmpeg não está instalado."
    echo "    Instala com: pip install imageio-ffmpeg"
    echo "    Sem isto, ficheiros MP3/AAC NÃO poderão ser analisados no bundle."
    exit 1
fi
echo "    imageio-ffmpeg: OK"

# Generate icon assets
python3 "${PROJECT_ROOT}/tools/generate_icons.py" 2>/dev/null || \
    echo "    AVISO: Geração de ícones falhou. Continuando com ícones existentes..."
echo ""

# ---------------------------------------------------------------------------
# Step 1 — Verify / install PyInstaller
# ---------------------------------------------------------------------------
echo "[1/6] Verificando PyInstaller..."
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
echo "[2/6] Verificando create-dmg..."
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
echo "[3/6] A limpar builds anteriores..."
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
echo "[4/6] A correr PyInstaller..."

# Build extra args for architecture targeting
PYINSTALLER_EXTRA_ARGS=""
if [ -n "${TARGET_ARCH}" ]; then
    PYINSTALLER_EXTRA_ARGS="--target-architecture ${TARGET_ARCH}"
fi

# shellcheck disable=SC2086
pyinstaller camel_hot.spec --clean --noconfirm ${PYINSTALLER_EXTRA_ARGS}

if [ ! -d "dist/CamelHot.app" ]; then
    echo ""
    echo "    ERRO: dist/CamelHot.app não foi criado."
    echo "    Consulta o output do PyInstaller acima."
    exit 1
fi
echo "    OK — dist/CamelHot.app criado."
"dist/CamelHot.app/Contents/MacOS/CamelHot" --smoke-test
echo "    OK — runtime de análise empacotado validado."
echo ""

# ---------------------------------------------------------------------------
# Step 5 — Remove Gatekeeper quarantine from the built .app
# ---------------------------------------------------------------------------
echo "[5/6] A remover atributo de quarentena do Gatekeeper..."
xattr -dr com.apple.quarantine "dist/CamelHot.app" 2>/dev/null && \
    echo "    Quarentena removida." || \
    echo "    Nenhum atributo de quarentena encontrado (OK)."
echo ""

if [ -n "${MACOS_CODESIGN_IDENTITY:-}" ]; then
    echo "    A assinar a aplicação..."
    codesign --force --deep --options runtime --timestamp \
        --sign "${MACOS_CODESIGN_IDENTITY}" "dist/CamelHot.app"
    codesign --verify --deep --strict --verbose=2 "dist/CamelHot.app"
    echo "    Assinatura validada."

    if [ -n "${APPLE_ID:-}" ] && [ -n "${APPLE_TEAM_ID:-}" ] && [ -n "${APPLE_APP_PASSWORD:-}" ]; then
        echo "    A submeter para notarização..."
        NOTARIZATION_ZIP="dist/CamelHot-notarization.zip"
        rm -f "${NOTARIZATION_ZIP}"
        ditto -c -k --keepParent "dist/CamelHot.app" "${NOTARIZATION_ZIP}"
        xcrun notarytool submit "${NOTARIZATION_ZIP}" --wait \
            --apple-id "${APPLE_ID}" --team-id "${APPLE_TEAM_ID}" --password "${APPLE_APP_PASSWORD}"
        xcrun stapler staple "dist/CamelHot.app"
        spctl --assess --type execute --verbose=4 "dist/CamelHot.app"
        rm -f "${NOTARIZATION_ZIP}"
        echo "    Notarização validada."
    else
        echo "    AVISO: Credenciais de notarização ausentes; artefacto não será distribuível via Gatekeeper."
        if [ "${REQUIRE_MACOS_NOTARIZATION:-false}" = "true" ]; then
            exit 1
        fi
    fi
else
    echo "    AVISO: MACOS_CODESIGN_IDENTITY não definida; artefacto não assinado."
    if [ "${REQUIRE_MACOS_NOTARIZATION:-false}" = "true" ]; then
        exit 1
    fi
fi
echo ""

# ---------------------------------------------------------------------------
# Step 6 — Create .dmg
# ---------------------------------------------------------------------------
echo "[6/6] A criar imagem de disco .dmg..."

if [ "${CREATE_DMG_AVAILABLE:-true}" = "false" ]; then
    echo "    A saltar criação do .dmg (create-dmg não disponível)."
    echo ""
    echo "============================================================"
    echo "  Build concluído (sem .dmg)."
    echo "  App em: dist/CamelHot.app"
    echo ""
    echo "  NOTA: Define MACOS_CODESIGN_IDENTITY e credenciais Apple para distribuição."
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
echo "  Ficheiro: dist/CamelHot.dmg  (${DMG_SIZE})"
echo ""
echo "  DISTRIBUIÇÃO:"
echo "  - Releases públicas devem definir MACOS_CODESIGN_IDENTITY e credenciais Apple."
echo "  - Para build universal (Intel+ARM): ARCH=universal2 bash $0"
echo "============================================================"

