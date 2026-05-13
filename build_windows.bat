@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   Compilador DMMView para Windows (Standalone .exe)
echo ========================================================
echo.

:: Detectar comando de Python (python o python3)
set PYTHON_CMD=python
%PYTHON_CMD% --version >nul 2>&1
if !errorlevel! neq 0 (
    set PYTHON_CMD=python3
    !PYTHON_CMD! --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo [ERROR] No se encontro 'python' ni 'python3'.
        echo Por favor, instala Python 3.10+ y asegurate de que este en el PATH.
        pause
        exit /b 1
    )
)

echo [INFO] Usando comando: %PYTHON_CMD%
%PYTHON_CMD% --version

:: Extraer version del codigo
for /f "tokens=*" %%a in ('%PYTHON_CMD% -c "import sys; sys.path.insert(0, '.'); from core.version import VERSION; print(VERSION)"') do set APP_VERSION=%%a
set VERSION_CLEAN=%APP_VERSION:.=_%
set EXE_NAME=DMMView%VERSION_CLEAN%

echo [INFO] Detectada Version: %APP_VERSION%
echo [INFO] El archivo sera: %EXE_NAME%.exe

:: Instalar dependencias
echo [1/3] Actualizando pip e instalando dependencias...
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install -r requirements.txt
%PYTHON_CMD% -m pip install pyinstaller

:: Limpiar compilaciones anteriores
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

:: Compilar usando PyInstaller
echo [2/3] Compilando %EXE_NAME% a ejecutable. Esto tomara un minuto...
:: --noconfirm: Sobrescribir sin preguntar
:: --windowed: Ocultar la consola (GUI app)
:: --onefile: Empaquetar todo en un solo .exe
:: --collect-submodules: Asegurar que se incluyan todos los modulos internos
%PYTHON_CMD% -m PyInstaller --noconfirm --windowed --onefile ^
    --name "%EXE_NAME%" ^
    --icon="ui/icon.png" ^
    --add-data "ui/icon.png;ui" ^
    --hidden-import="PyQt6.QtSvg" ^
    --collect-submodules plugins ^
    --collect-submodules ui ^
    --collect-submodules core ^
    dmmwin.py

if !errorlevel! neq 0 (
    echo [ERROR] Hubo un problema durante la compilacion.
    pause
    exit /b 1
)

:: Finalizado
echo [3/3] ¡Proceso Completado con Exito!
echo.
echo Encontraras tu programa %EXE_NAME%.exe dentro de la carpeta "dist".
echo Puedes copiar ese archivo a cualquier otra PC con Windows 10/11.
echo.
pause
