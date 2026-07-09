@echo off
title DJ Harmonic Analyzer — Instalador
chcp 65001 >nul

echo.
echo  =====================================================
echo   DJ Harmonic Analyzer
echo  =====================================================
echo.

:: ---- Verificar Python -------------------------------------------------------
where python >nul 2>&1
if errorlevel 1 (
    echo  [ERRO] Python nao encontrado no PATH.
    echo.
    echo  Por favor instala Python 3.8+ em:
    echo    https://www.python.org/downloads/
    echo.
    echo  Certifica-te de marcar "Add Python to PATH" durante a instalacao.
    echo.
    pause
    start https://www.python.org/downloads/
    exit /b 1
)

:: ---- Verificar versao minima ------------------------------------------------
python -c "import sys; exit(0 if sys.version_info >= (3,8) else 1)" >nul 2>&1
if errorlevel 1 (
    echo  [ERRO] Python 3.8 ou superior necessario.
    for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo  Versao atual: %%i
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo  Usando: %%i

:: ---- Bootstrap PyQt5 (necessario para abrir o installer GUI) ----------------
echo.
echo  A verificar PyQt5...
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo  Instalando PyQt5 para o instalador grafico...
    python -m pip install "PyQt5>=5.15.0" --quiet
    if errorlevel 1 (
        echo  [ERRO] Falha ao instalar PyQt5. Verifica a tua ligacao a internet.
        pause
        exit /b 1
    )
)

:: ---- Windows audio stack ----------------------------------------------------
:: soundfile   - bundles libsndfile64bit.dll for WAV/FLAC on Windows
:: imageio-ffmpeg - ships a static ffmpeg binary; required for MP3/AAC/OGG
:: audioread   - multi-backend audio loader used by librosa
echo.
echo  Instalando dependencias de audio para Windows...

python -m pip install "soundfile>=0.12.0" --quiet
if errorlevel 1 (
    echo  [AVISO] Falha ao instalar soundfile.
)

python -m pip install "imageio-ffmpeg>=0.5.0" --quiet
if errorlevel 1 (
    echo  [ERRO CRITICO] Falha ao instalar imageio-ffmpeg.
    echo  Sem imageio-ffmpeg, ficheiros MP3 NAO podem ser analisados.
    echo  Verifica a tua ligacao a internet e volta a tentar.
    pause
    exit /b 1
)

python -m pip install "audioread>=3.0.0" --quiet
if errorlevel 1 (
    echo  [AVISO] Falha ao instalar audioread.
)

:: ---- Health check: verify complete audio stack ------------------------------
echo.
echo  Verificando stack de audio completo...
python -c "import librosa, soundfile, imageio_ffmpeg; print('OK')" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERRO] Stack de audio incompleto.
    echo.
    echo  Solucao manual:
    echo    pip install librosa soundfile imageio-ffmpeg audioread
    echo.
    echo  O instalador grafico tentara corrigir isto automaticamente.
    echo.
    pause
)

:: ---- Lançar installer GUI ---------------------------------------------------
echo  Abrindo instalador...
echo.
python "%~dp0installer.py"
exit /b %ERRORLEVEL%

