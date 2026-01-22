@echo off
echo DESLIGANDO O SISTEMA ARGUS...
echo.

:: Mata todos os processos Python (Cuidado se ele usar python pra outra coisa)
taskkill /F /IM python.exe /T

echo.
echo [SISTEMA OFF] Tudo desligado.
pause