@echo off
setlocal
title Instalador Argus Voice (Kokoro)

echo [ARGUS VOICE] Iniciando instalacao do Modulo Vocal...
echo.

:: 1. Instalar o uv (Versão Windows via PowerShell)
echo [1/3] Verificando UV...
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo UV nao encontrado. Instalando via PowerShell...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    echo.
    echo [NOTA] Se o 'uv' nao for reconhecido abaixo, reinicie o terminal apos isso.
) else (
    echo [OK] UV ja instalado.
)

:: 2. Instalar Dependencias Python
echo.
echo [2/3] Instalando bibliotecas Python...
call venv\Scripts\activate

:: Tentativa com UV (Se estiver no PATH)
echo Tentando instalar com UV...
uv pip install kokoro>=0.9.4 soundfile>=0.13.1 sounddevice numpy>=1.24.0 torch scipy

:: Se o UV falhar (porque acabou de instalar e nao ta no PATH), usa o PIP normal como garantia
if %errorlevel% neq 0 (
    echo [AVISO] UV nao encontrado no PATH (normal na 1a vez).
    echo Usando PIP padrao para garantir...
    pip install kokoro>=0.9.4 soundfile>=0.13.1 sounddevice numpy>=1.24.0 torch scipy
)

:: 3. Verificar e Instalar eSpeak-ng
echo.
echo [3/3] Verificando eSpeak-ng (Motor de Fonetizacao)...

:: Verifica Program Files normal e (x86)
set "ESPEAK_PATH=C:\Program Files\eSpeak NG\espeak-ng.exe"
if not exist "%ESPEAK_PATH%" (
    set "ESPEAK_PATH=C:\Program Files (x86)\eSpeak NG\espeak-ng.exe"
)

if not exist "%ESPEAK_PATH%" (
    echo [AVISO] eSpeak-ng nao encontrado!
    echo Baixando instalador MSI...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/espeak-ng/espeak-ng/releases/download/1.51/espeak-ng-X64.msi' -OutFile 'espeak_installer.msi'"
    
    echo.
    echo ========================================================
    echo [ATENCAO] A janela de instalacao vai abrir agora.
    echo 1. Siga o instalador (Next, Next, Install).
    echo 2. IMPORTANTE: Apos instalar, REINICIE O COMPUTADOR ou o VS CODE.
    echo ========================================================
    echo.
    start espeak_installer.msi
    pause
) else (
    echo [OK] eSpeak-ng detectado.
)

echo.
echo [CONCLUIDO] Tudo pronto. Pode fechar.
pause