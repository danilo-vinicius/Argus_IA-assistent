@echo off
echo ==========================================
echo      INSTALADOR DO SISTEMA ARGUS v2.5
echo ==========================================
echo.

:: 1. Verifica se Python existe
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado! Instale o Python antes de continuar.
    pause
    exit /b
)

:: 2. Cria Ambiente Virtual
echo [1/3] Criando ambiente virtual (VENV)...
python -m venv venv

:: 3. Ativa e Instala Dependencias
echo [2/3] Instalando bibliotecas neurais...
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

:: 4. Finalização
echo.
echo [3/3] Instalacao concluida!
echo.
echo Para iniciar o Argus, use o arquivo 'run.bat'.
echo ==========================================
pause