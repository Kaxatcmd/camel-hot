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

:: ---- Lançar installer GUI ---------------------------------------------------
echo  Abrindo instalador...
echo.
python "%~dp0installer.py"
exit /b %ERRORLEVEL%
