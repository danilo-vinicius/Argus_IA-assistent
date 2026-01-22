@echo off
TITLE ARGUS LAUNCHER

echo ===================================================
echo    INICIANDO ARGUS SYSTEM (Always On Mode)
echo ===================================================

call venv\Scripts\activate

:: 1. Cérebro (Orquestrador + Voz)
start "ARGUS BRAIN" cmd /k "python app.py"

:: 2. Audição (Sempre ouvindo)
start "ARGUS EARS" cmd /k "python core/listen_core.py"

:: 3. Visão (Continua manual pelo site, pois gasta muita bateria/processamento)
:: (Nenhuma linha aqui, o site cuida disso)

echo.
echo [SISTEMA ONLINE] Acessar: http://localhost:5000
pause