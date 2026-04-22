@echo off
title DocShare Multi Server

echo ===============================
echo Iniciando DocShare...
echo ===============================

:: Mata processos antigos
echo Limpando instâncias antigas...
taskkill /F /IM python.exe >nul 2>&1

timeout /t 1 > nul

:: Servidor 8080
echo Iniciando servidor 8080...
start "DocShare-8080" cmd /c "cd /d %~dp0 && python Server.py 8080"

timeout /t 2 > nul

:: Servidor 8081
echo Iniciando servidor 8081...
start "DocShare-8081" cmd /c "cd /d %~dp0 && python Server.py 8081"

timeout /t 2 > nul

:: Servidor 8082
echo Iniciando servidor 8082...
start "DocShare-8082" cmd /c "cd /d %~dp0 && python Server.py 8082"

timeout /t 2 > nul

:: Abre no navegador
start http://localhost:8000
start http://localhost:8001
start http://localhost:8002

echo.
echo Servidores iniciados com sucesso!
echo - http://localhost:8000 (WS: 8080)
echo - http://localhost:8001 (WS: 8081)
echo - http://localhost:8002 (WS: 8082)
echo.
pause
