@echo off
echo Iniciando múltiplas instâncias do servidor DocShare...

echo Iniciando servidor na porta 8080...
start "DocShare-8080" cmd /c "cd /d %~dp0 && python Server.py 8080"

timeout /t 2 /nobreak > nul

echo Iniciando servidor na porta 8081...
start "DocShare-8081" cmd /c "cd /d %~dp0 && python Server.py 8081"

timeout /t 2 /nobreak > nul

echo Iniciando servidor na porta 8082...
start "DocShare-8082" cmd /c "cd /d %~dp0 && python Server.py 8082"

echo.
echo Servidores iniciados!
echo - Porta 8080: http://localhost:8000 (WebSocket: ws://localhost:8080)
echo - Porta 8081: http://localhost:8000 (WebSocket: ws://localhost:8081)
echo - Porta 8082: http://localhost:8000 (WebSocket: ws://localhost:8082)
echo.
echo Cada cliente pode escolher qual porta usar na tela de entrada.
pause