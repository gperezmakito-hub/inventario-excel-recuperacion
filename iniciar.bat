@echo off
echo ========================================
echo   INVENTARIO TINTAS - Iniciando...
echo ========================================
echo.

cd /d "%~dp0"

echo Verificando entorno virtual...
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: No se encuentra el entorno virtual.
    echo Ejecuta primero: python -m venv .venv
    echo Luego: .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo Iniciando servidor Flask...
echo.
echo ----------------------------------------
echo   Abre tu navegador en:
echo   http://127.0.0.1:5000
echo.
echo   Usuario: admin
echo   Password: admin123
echo ----------------------------------------
echo.
echo Pulsa Ctrl+C para detener el servidor.
echo.

.venv\Scripts\python.exe run.py
