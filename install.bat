@echo off
echo ==========================================
echo    ATUALIZADOR ARGUS (MODO INTELIGENTE)
echo ==========================================
echo.

:: 1. Verifica se a VENV já existe
if exist "venv" (
    echo [INFO] Ambiente virtual encontrado. Verificando atualizacoes...
) else (
    echo [AVISO] Ambiente nao encontrado. Criando VENV do zero...
    :: Tenta criar com Python 3.11 ou o padrão do sistema
    py -3.11 -m venv venv || python -m venv venv
)

:: 2. Instalação / Atualização
echo [2/3] Sincronizando bibliotecas...
echo.

:: Atualiza o pip (rápido e seguro)
"venv\Scripts\python.exe" -m pip install --upgrade pip

:: O segredo: O pip vai ler o arquivo e pular o que já está instalado!
"venv\Scripts\python.exe" -m pip install -r requirements.txt

:: GARANTIA PARA O VISION CORE (Trava o Numpy na versão certa)
"venv\Scripts\python.exe" -m pip install "numpy<2.0.0"

:: 3. Verificação
echo.
echo [3/3] Checagem final...
if exist "venv\Lib\site-packages\flask" (
    echo [SUCESSO] Dependencias do Argus estao OK!
) else (
    echo [ERRO] Falha na instalacao. Verifique o log acima.
)

echo.
echo Pode rodar o 'run.bat' sem medo.
echo ==========================================
pause