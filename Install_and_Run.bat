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
:: soundfile  → bundles libsndfile64bit.dll for Windows
:: imageio-ffmpeg → static ffmpeg binary detected automatically by librosa
:: audioread  → Windows audio backend fallback (WMF/GStreamer)
echo.
echo  Instalando dependencias de audio para Windows...
python -m pip install soundfile --quiet
if errorlevel 1 (
    echo  [AVISO] Falha ao instalar soundfile. Verifique a ligacao a internet.
)
python -m pip install imageio-ffmpeg --quiet
if errorlevel 1 (
    echo  [AVISO] Falha ao instalar imageio-ffmpeg. Verifique a ligacao a internet.
)
python -m pip install audioread --quiet
if errorlevel 1 (
    echo  [AVISO] Falha ao instalar audioread. Verifique a ligacao a internet.
)

:: ---- Health check: verify librosa + soundfile are importable ----------------
echo.
echo  Verificando stack de audio (librosa + soundfile)...
python -c "import librosa, soundfile; librosa.load" >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [ERRO] Stack de audio nao disponivel apos instalacao.
    echo.
    echo  Possíveis causas:
    echo    - librosa nao esta instalado ^(sera instalado pelo instalador grafico^)
    echo    - soundfile ou libsndfile64bit.dll em falta
    echo    - Dependencias corrompidas
    echo.
    echo  Execute o instalador grafico que se abrira a seguir.
    echo  Se o problema persistir, execute manualmente:
    echo    pip install librosa soundfile imageio-ffmpeg audioread
    echo.
    pause
)

:: ---- Lançar installer GUI ---------------------------------------------------
echo  Abrindo instalador...
echo.
python "%~dp0installer.py"
exit /b %ERRORLEVEL%
