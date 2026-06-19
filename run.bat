@echo off
title RiskVision Launcher - Venezuela Bank Data
color 0B

echo ==========================================================
echo               RiskVision - Control de Riesgos
echo ==========================================================
echo.
echo [1] Ejecutar Servidor Visualizador (FastAPI)
echo [2] Volver a Generar Base de Datos (SQLite + Postgres SQL)
echo [3] Salir
echo.
set /p opt="Seleccione una opcion [1-3]: "

if "%opt%"=="2" (
    echo.
    echo [+] Iniciando generador de datos bancarios...
    C:\python_embedded\python.exe database\db_generator.py
    echo.
    echo [+] Base de datos generada exitosamente.
    pause
    goto start_app
)

if "%opt%"=="1" (
    goto start_app
)

goto end

:start_app
echo.
echo [+] Iniciando servidor FastAPI en http://127.0.0.1:8000 ...
echo [+] Presione Ctrl+C para detener el servidor.
echo.
start http://127.0.0.1:8000
C:\python_embedded\python.exe -m uvicorn visualizer.app:app --host 127.0.0.1 --port 8000 --reload
goto end

:end
echo.
echo Gracias por usar RiskVision. Saliendo...
pause
