@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

echo ============================================================
echo   CAMEL-HOT — Utilitario: Copiar libs VLC (Windows)
echo ============================================================
echo.
echo   Este script copia as bibliotecas nativas do VLC para
echo   vlc_libs\ para serem incluidas no build do PyInstaller.
echo.

set TARGET_DIR=%~dp0..\vlc_libs
set FOUND=0

:: ---------------------------------------------------------------------------
:: Procurar VLC em locais comuns
:: ---------------------------------------------------------------------------
echo [1/2] A procurar VLC instalado...

set VLC_PATHS[0]=C:\Program Files\VideoLAN\VLC
set VLC_PATHS[1]=C:\Program Files (x86)\VideoLAN\VLC

for /l %%i in (0,1,1) do (
    set "_path=!VLC_PATHS[%%i]!"
    if exist "!_path!\libvlc.dll" (
        echo     VLC encontrado em: !_path!
        set VLC_DIR=!_path!
        set FOUND=1
        goto :found
    )
)

echo     VLC nao encontrado nos locais padrao.
echo.
echo     Por favor, instala o VLC Media Player:
echo       https://www.videolan.org/vlc/download-windows.html
echo.
echo     Apos instalar, volta a correr este script.
echo.
pause
exit /b 1

:found
echo.

:: ---------------------------------------------------------------------------
:: Copiar libs para vlc_libs/
:: ---------------------------------------------------------------------------
echo [2/2] A copiar libs para vlc_libs\...

if not exist "%TARGET_DIR%" (
    mkdir "%TARGET_DIR%"
    echo     Pasta vlc_libs\ criada.
)

:: Copiar DLLs principais
echo     A copiar libvlc.dll...
copy /y "%VLC_DIR%\libvlc.dll" "%TARGET_DIR%\" >nul
echo     A copiar libvlccore.dll...
copy /y "%VLC_DIR%\libvlccore.dll" "%TARGET_DIR%\" >nul

:: Copiar pasta plugins (necessaria para reproducao de audio)
if exist "%VLC_DIR%\plugins" (
    echo     A copiar pasta plugins\ (pode demorar alguns segundos)...
    if exist "%TARGET_DIR%\plugins" rmdir /s /q "%TARGET_DIR%\plugins"
    xcopy /e /i /q "%VLC_DIR%\plugins" "%TARGET_DIR%\plugins" >nul
    echo     Pasta plugins copiada.
) else (
    echo     AVISO: Pasta plugins nao encontrada em %VLC_DIR%
    echo     A reproducao de audio pode nao funcionar corretamente.
)

echo.
echo ============================================================
echo   VLC libs copiadas para vlc_libs\ — pronto para build!
echo.
echo   Ficheiros copiados:
echo     vlc_libs\libvlc.dll
echo     vlc_libs\libvlccore.dll
echo     vlc_libs\plugins\  (pasta completa)
echo.
echo   Passo seguinte: corre build_windows\build.bat
echo ============================================================
pause
