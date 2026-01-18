@echo off
title ARGUS SYSTEM v2.5
echo.
echo [SISTEMA] Iniciando Argus...
if not exist "venv\Scripts\python.exe" (
    echo [ERRO] Rode o install.bat primeiro!
    pause
    exit /b
)
start http://127.0.0.1:5000
"venv\Scripts\python.exe" app.py
pause