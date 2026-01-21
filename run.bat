@echo off
TITLE ARGUS LAUNCHER

echo ===================================================
echo    INICIANDO ARGUS SYSTEM (Brain + Vision + Voice)
echo ===================================================

:: 1. Ativa o ambiente virtual
call venv\Scripts\activate

:: 2. Inicia o Servidor (Cérebro + Voz TTS)
start "ARGUS BRAIN" cmd /k "python app.py"

:: Aguarda o servidor subir um pouco
timeout /t 5

:: 3. Inicia a Visão (Gesto)
start "ARGUS EYES" cmd /k "python vision_core.py"

:: 4. Inicia a Audição (Whisper) - NOVO!
start "ARGUS EARS" cmd /k "python listen_core.py"

echo.
echo [SISTEMA ONLINE]
echo Fale com o Argus ou use gestos.
echo.
pause