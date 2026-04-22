#!/bin/bash
# Script para Linux/Mac - iniciar múltiplas instâncias do servidor

echo "Iniciando múltiplas instâncias do servidor DocShare..."

echo "Iniciando servidor na porta 8080..."
python3 Server.py 8080 &

sleep 2

echo "Iniciando servidor na porta 8081..."
python3 Server.py 8081 &

sleep 2

echo "Iniciando servidor na porta 8082..."
python3 Server.py 8082 &

echo ""
echo "Servidores iniciados!"
echo "- Porta 8080: http://localhost:8000 (WebSocket: ws://localhost:8080)"
echo "- Porta 8081: http://localhost:8000 (WebSocket: ws://localhost:8081)"
echo "- Porta 8082: http://localhost:8000 (WebSocket: ws://localhost:8082)"
echo ""
echo "Cada cliente pode escolher qual porta usar na tela de entrada."