@echo off
echo ================================
echo   Inventario Tintas - Setup
echo ================================
echo.

REM Verificar si existe entorno virtual
if not exist ".venv" (
    echo Creando entorno virtual...
    python -m venv .venv
)

echo Activando entorno virtual...
call .venv\Scripts\activate.bat

echo Instalando dependencias...
pip install -r requirements.txt

echo.
echo ================================
echo   Configuración completada
echo ================================
echo.
echo Para ejecutar la migración desde Excel:
echo   python scripts\migrar_excel.py
echo.
echo Para ejecutar la aplicación:
echo   python run.py
echo.
echo Luego abre: http://localhost:5000
echo.
