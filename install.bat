@echo off
echo ==========================================
echo    INSTALADOR ARGUS (MODO RESOLUCAO)
echo ==========================================
echo.

:: 1. Limpa instalação anterior com conflito
if exist "venv" (
    echo [INFO] Apagando ambiente com conflito...
    rmdir /s /q venv
)

:: 2. Cria o ambiente (Prioriza Python 3.11 se tiver)
echo [1/3] Criando VENV...
py -3.11 -m venv venv || python -m venv venv

:: 3. Instalação
echo [2/3] Baixando bibliotecas compativeis...
echo.

:: Atualiza pip (Crucial para resolver dependencias novas)
"venv\Scripts\python.exe" -m pip install --upgrade pip

:: Instala requirements.txt
"venv\Scripts\python.exe" -m pip install -r requirements.txt

:: 4. Verificação
echo.
echo [3/3] Verificando instalacao...
if exist "venv\Lib\site-packages\flask" (
    echo [SUCESSO] Flask encontrado!
    echo [SUCESSO] LangChain instalado!
) else (
    echo [ERRO] Falha na instalacao. Verifique o log acima.
)

echo.
echo Agora pode rodar o 'run.bat'.
echo ==========================================
pause