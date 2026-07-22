@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo ============================================================
echo   CAMEL-HOT — Windows Build Script
echo ============================================================
echo.

:: ---------------------------------------------------------------------------
:: Step 0 — Verify critical build dependencies
:: ---------------------------------------------------------------------------
echo [0/5] Verificando dependencias de build...
cd /d "%~dp0.."

:: imageio-ffmpeg MUST be installed before building
python -c "import imageio_ffmpeg" >nul 2>&1
if errorlevel 1 (
    echo     ERRO: imageio-ffmpeg nao esta instalado.
    echo     Sem isto, ficheiros MP3/AAC NAO poderao ser analisados no bundle.
    echo     A instalar agora...
    pip install "imageio-ffmpeg>=0.5.0"
    if errorlevel 1 (
        echo     ERRO: Falha ao instalar imageio-ffmpeg. Verifica a internet.
        pause
        exit /b 1
    )
    echo     imageio-ffmpeg instalado.
) else (
    echo     imageio-ffmpeg: OK
)

:: soundfile must also be present
python -c "import soundfile" >nul 2>&1
if errorlevel 1 (
    echo     Instalando soundfile...
    pip install "soundfile>=0.12.0"
)

:: librosa MUST be installed — it is the core audio analysis engine
python -c "import librosa" >nul 2>&1
if errorlevel 1 (
    echo     ERRO: librosa nao esta instalado.
    echo     Sem isto, a analise de audio NAO funcionara no bundle.
    echo     A instalar agora...
    pip install "librosa>=0.10.0"
    if errorlevel 1 (
        echo     ERRO: Falha ao instalar librosa. Verifica a internet.
        pause
        exit /b 1
    )
    echo     librosa instalado.
) else (
    echo     librosa: OK
)

:: Generate icon assets (requires Pillow)
echo.
echo     Gerando icones...
python tools\generate_icons.py
if errorlevel 1 (
    echo     AVISO: Geracao de icones falhou. Continuando com icones existentes...
)
echo.

:: ---------------------------------------------------------------------------
:: Step 1 — Verify / install PyInstaller
:: ---------------------------------------------------------------------------
echo [1/5] Verificando PyInstaller...
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo     PyInstaller nao encontrado. A instalar...
    pip install pyinstaller
    if errorlevel 1 (
        echo     ERRO: Falha ao instalar PyInstaller.
        echo     Certifica-te de que o Python e o pip estao no PATH.
        pause
        exit /b 1
    )
    echo     PyInstaller instalado com sucesso.
) else (
    for /f "delims=" %%v in ('pyinstaller --version 2^>nul') do echo     Versao: %%v
)
echo.

:: ---------------------------------------------------------------------------
:: Step 2 — Clean dist/ folder
:: ---------------------------------------------------------------------------
echo [2/5] A limpar pasta dist/...
set DIST_DIR=%~dp0..\dist
if exist "%DIST_DIR%\CamelHot" (
    rmdir /s /q "%DIST_DIR%\CamelHot"
    echo     dist\CamelHot removido.
)
if exist "%DIST_DIR%\CamelHot_Setup.exe" (
    del /q "%DIST_DIR%\CamelHot_Setup.exe"
    echo     dist\CamelHot_Setup.exe removido.
)
echo.

:: ---------------------------------------------------------------------------
:: Step 3 — Run PyInstaller
:: ---------------------------------------------------------------------------
echo [3/5] A correr PyInstaller...
cd /d "%~dp0.."
pyinstaller camel_hot.spec --clean --noconfirm
if errorlevel 1 (
    echo.
    echo     ERRO: PyInstaller falhou. Consulta o output acima.
    pause
    exit /b 1
)
echo.

:: ---------------------------------------------------------------------------
:: Step 4 — Verify output
:: ---------------------------------------------------------------------------
echo [4/5] A verificar output...
if exist "%DIST_DIR%\CamelHot\CamelHot.exe" (
    echo     OK — dist\CamelHot\CamelHot.exe encontrado.
) else (
    echo     ERRO: dist\CamelHot\CamelHot.exe NAO encontrado.
    echo     Verifica os erros do PyInstaller acima.
    pause
    exit /b 1
)
echo.

:: ---------------------------------------------------------------------------
:: Step 5 — Inno Setup (cria instalador .exe)
:: ---------------------------------------------------------------------------
echo [5/5] A criar instalador com Inno Setup...
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if exist %ISCC% (
    %ISCC% "%~dp0setup.iss"
    if errorlevel 1 (
        echo     ERRO: Inno Setup falhou. Consulta o output acima.
        pause
        exit /b 1
    )
    echo.
    echo     OK — CamelHot_Setup.exe criado em dist\
) else (
    echo     AVISO: Inno Setup 6 nao encontrado.
    echo.
    echo     Para criar o instalador .exe, instala o Inno Setup 6:
    echo       https://jrsoftware.org/isdl.php
    echo.
    echo     Apos instalar, volta a correr este script,
    echo     ou corre manualmente:
    echo       "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" build_windows\setup.iss
    echo.
    echo     O build do PyInstaller esta em dist\CamelHot\ e pode
    echo     ser usado diretamente sem instalador.
)

echo.
echo ============================================================
echo   Build concluido.
echo ============================================================
pause
