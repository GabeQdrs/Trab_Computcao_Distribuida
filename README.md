# DocShare - Editor Colaborativo em Tempo Real

Editor de texto colaborativo estilo Google Docs, desenvolvido com WebSockets em Python e JavaScript.

## Funcionalidades

- Edição colaborativa em tempo real
- Validação case-insensitive de nicknames
- Gerenciamento de arquivos (criar/deletar/clonar/renomear)
- Persistência automática de documentos
- Interface moderna e responsiva
- **Suporte a múltiplas portas WebSocket**

## Como executar

### Opção 1: Servidor único (porta padrão 8080)
```bash
python Server.py
```

### Opção 2: Servidor em porta específica
```bash
python Server.py 8081
```

### Opção 3: Múltiplas instâncias (recomendado para testes)
```bash
# Windows
start_servers.bat

# Linux/Mac
chmod +x start_servers.sh
./start_servers.sh

# Ou manualmente:
python Server.py 8080 &
python Server.py 8081 &
python Server.py 8082 &
```

## Acesso

Após iniciar o servidor no PC servidor:

1. Abra `http://localhost:8000` no navegador do próprio servidor
2. Digite seu nickname
3. Clique em "Entrar"

### Uso em rede local com 2 PCs

Se você for apresentar em dois computadores na mesma rede:

1. No PC servidor, execute `python server.py`
2. Verifique o endereço IP do servidor na rede local (por exemplo, `192.168.0.10`)
3. No segundo PC, abra `http://<IP-do-servidor>:8000` no navegador
4. Digite outro nickname e clique em "Entrar"

O cliente agora usa automaticamente o host que serviu a página para conectar o WebSocket, então não é necessário alterar o código no navegador.

### Nota

- O `server.py` agora aceita conexões de outros PCs porque o WebSocket está ligado em `0.0.0.0`.
- O HTTP também funciona em rede local, então o segundo PC pode carregar o site diretamente do servidor.

**Sistema automático**: Se a porta inicial não estiver disponível, o cliente tentará automaticamente portas sequenciais (8081, 8082, etc.) até encontrar um servidor ativo.

## 🔌 Sistema de Portas Automático

- **Descoberta automática**: Cliente tenta portas sequenciais até conectar
- **Timeout**: 2 segundos por tentativa de conexão
- **Reconexão**: Em caso de desconexão, tenta reconectar na mesma porta
- **Fallback**: Se nickname rejeitado, tenta automaticamente próxima porta
- **Display**: Mostra a porta atual conectada no header

### Exemplo de funcionamento:

1. Cliente tenta conectar na porta 8080
2. Se falhar (timeout), tenta 8081
3. Se conseguir conectar mas nickname estiver em uso, tenta 8082
4. Continua até encontrar uma combinação válida

## Estrutura do projeto

```
Trab_Computcao_Distribuida/
├── Server.py              # Servidor WebSocket + HTTP
├── index.html            # Interface do cliente
├── documents.json        # Persistência de arquivos
└── start_servers.bat     # Script para múltiplas instâncias
```

## Troubleshooting

### Porta ocupada
```bash
# Verificar processos na porta
netstat -ano | findstr :8080

# Matar processo
taskkill /PID <PID> /F
```

### Erro de conexão
- Verifique se o servidor está rodando
- Confirme a porta WebSocket no cliente
- Verifique se não há firewall bloqueando

## Desenvolvimento

- **Python**: 3.8+
- **WebSockets**: Biblioteca `websockets`
- **Cliente**: JavaScript nativo (sem frameworks)

## Casos de uso

- **Desenvolvimento**: Testes com múltiplas instâncias
- **Produção**: Balanceamento de carga com portas diferentes
- **Debugging**: Isolamento de sessões de colaboração
