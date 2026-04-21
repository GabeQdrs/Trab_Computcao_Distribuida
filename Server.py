import asyncio
import json
import websockets
import threading
import http.server
import socketserver
import os
from datetime import datetime

# Arquivo de persistência
DATA_FILE = 'documents.json'

# Estado global dos arquivos
files = {}

def load_files():
    """Carrega arquivos do arquivo de persistência."""
    global files
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                files = json.load(f)
            print(f"Arquivos carregados do {DATA_FILE}")
        except Exception as e:
            print(f"Erro ao carregar arquivos: {e}")
            files = {"Document1": ""}
    else:
        files = {"Document1": ""}
    
    # Garante que "Document1" sempre existe
    if "Document1" not in files:
        files["Document1"] = ""
        save_files()

def save_files():
    """Salva arquivos no arquivo de persistência."""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(files, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar arquivos: {e}")

# Conjunto de conexões WebSocket com nicknames
connected_clients = {}  # {websocket: {"nickname": "...", "current_file": "..."}}
nicknames_in_use = set()  # Nicknames ativos

async def broadcast(message, exclude_websocket=None):
    """Envia uma mensagem para todos os clientes conectados."""
    disconnected = []
    for client in list(connected_clients.keys()):
        if exclude_websocket and client == exclude_websocket:
            continue
        try:
            await client.send(message)
        except Exception as e:
            # Se falhar, marca para remover
            disconnected.append(client)
    
    # Remove clientes que falharam
    for client in disconnected:
        if client in connected_clients:
            nickname = connected_clients[client].get("nickname")
            del connected_clients[client]
            if nickname and nickname in nicknames_in_use:
                nicknames_in_use.discard(nickname)
            print(f"Cliente fantasma removido: {nickname}")

async def handler(websocket):
    """Manipula uma conexão WebSocket."""
    client_info = {"nickname": None, "current_file": "Document1"}
    # Não adiciona ainda - só após validação do nickname
    nickname_validated = False
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                
                # Primeiro, cliente escolhe nickname
                if "action" in data and data["action"] == "set_nickname":
                    nickname = data["nickname"].strip()
                    nickname_lower = nickname.lower()  # Para comparação case-insensitive
                    
                    # Valida se o nickname já está em uso (case-insensitive)
                    if nickname_lower in nicknames_in_use:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "Este apelido já está em uso. Escolha outro!"
                        }))
                        # Fecha a conexão se nickname inválido
                        await websocket.close()
                        return
                    
                    # Nickname válido - agora adiciona o cliente
                    client_info["nickname"] = nickname  # Mantém o case original para display
                    nicknames_in_use.add(nickname_lower)  # Armazena em lowercase
                    connected_clients[websocket] = client_info
                    nickname_validated = True
                    
                    print(f"Novo cliente conectado: {nickname}. Total: {len(connected_clients)}")
                    
                    # Notifica todos os clientes sobre a conexão
                    await broadcast(json.dumps({
                        "type": "client_joined",
                        "nickname": nickname,
                        "total_clients": len(connected_clients)
                    }))
                    # Envia lista de arquivos e conteúdo atual
                    await websocket.send(json.dumps({
                        "type": "files_list",
                        "files": list(files.keys())
                    }))
                    await websocket.send(json.dumps({
                        "type": "file_content",
                        "filename": "Document1",
                        "content": files.get("Document1", "")
                    }))
                
                # Só processa outras mensagens se nickname foi validado
                elif nickname_validated:
                    # Atualizar conteúdo do arquivo
                    if "type" in data and data["type"] == "text_update":
                        filename = data.get("filename", "Document1")
                        if filename in files:
                            files[filename] = data["content"]
                            save_files()
                            client_info["current_file"] = filename
                            # Broadcast para outros clientes
                            await broadcast(json.dumps({
                                "type": "file_content",
                                "filename": filename,
                                "content": files[filename],
                                "edited_by": client_info["nickname"]
                            }), exclude_websocket=websocket)
                    
                    # Criar novo arquivo
                    elif "type" in data and data["type"] == "create_file":
                        new_filename = data.get("filename", f"Document_{len(files)+1}")
                        if new_filename not in files:
                            files[new_filename] = ""
                            save_files()
                            await broadcast(json.dumps({
                                "type": "file_created",
                                "filename": new_filename,
                                "created_by": client_info["nickname"]
                            }))
                    
                    # Deletar arquivo
                    elif "type" in data and data["type"] == "delete_file":
                        filename = data.get("filename")
                        if filename in files:
                            del files[filename]
                            save_files()
                            # Se não houver mais arquivos, cria um novo Document1
                            if len(files) == 0:
                                files["Document1"] = ""
                                save_files()
                            await broadcast(json.dumps({
                                "type": "file_deleted",
                                "filename": filename,
                                "deleted_by": client_info["nickname"]
                            }))
                    
                    # Clonar arquivo
                    elif "type" in data and data["type"] == "clone_file":
                        original_filename = data.get("filename")
                        if original_filename in files:
                            clone_name = f"{original_filename}_copy_{len(files)}"
                            files[clone_name] = files[original_filename]
                            save_files()
                            await broadcast(json.dumps({
                                "type": "file_cloned",
                                "original": original_filename,
                                "clone": clone_name,
                                "cloned_by": client_info["nickname"]
                            }))
                    
                    # Renomear arquivo
                    elif "type" in data and data["type"] == "rename_file":
                        old_filename = data.get("old_filename")
                        new_filename = data.get("new_filename")
                        if old_filename in files and new_filename not in files and new_filename.strip():
                            files[new_filename] = files.pop(old_filename)
                            save_files()
                            await broadcast(json.dumps({
                                "type": "file_renamed",
                                "old_filename": old_filename,
                                "new_filename": new_filename,
                                "renamed_by": client_info["nickname"]
                            }))
                
                # Ignora mensagens se nickname não foi validado
                else:
                    print("Mensagem ignorada - nickname não validado")
                
            except json.JSONDecodeError:
                print("Mensagem JSON inválida recebida.")
    
    except websockets.exceptions.ConnectionClosed:
        nickname = client_info.get("nickname", "Desconhecido")
        print(f"Conexão fechada. Cliente: {nickname}")
    
    finally:
        if websocket in connected_clients:
            nickname = connected_clients[websocket].get("nickname", "Desconhecido")
            del connected_clients[websocket]
            if nickname != "Desconhecido":
                nicknames_in_use.discard(nickname.lower())  # Remove em lowercase
            if nickname != "Desconhecido":
                await broadcast(json.dumps({
                    "type": "client_left",
                    "nickname": nickname,  # Mantém o case original para broadcast
                    "total_clients": len(connected_clients)
                }))
            print(f"Cliente desconectado: {nickname}. Total de clientes: {len(connected_clients)}")
        elif not nickname_validated:
            print("Cliente desconectado sem validação de nickname")

def serve_html(port=8000):
    """Serve o arquivo index.html via HTTP."""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    handler_class = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler_class) as httpd:
        print(f"Servindo HTML em http://localhost:{port}")
        httpd.serve_forever()

import sys

async def main():
    # Carrega arquivos salvos
    load_files()
    
    # Verifica se foi passada uma porta como argumento
    port = 8080  # Porta padrão
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Porta inválida: {sys.argv[1]}. Usando porta padrão 8080.")
            port = 8080
    
    # Inicia o servidor WebSocket na porta especificada
    ws_server = await websockets.serve(handler, "localhost", port)
    print(f"Servidor WebSocket iniciado em ws://localhost:{port}")
    
    # Inicia o servidor HTTP em uma thread separada
    http_thread = threading.Thread(target=serve_html, daemon=True)
    http_thread.start()
    
    print(f"Servindo HTML em http://localhost:8000")
    print(f"Total de arquivos: {len(files)}")
    
    # Mantém o servidor rodando
    await ws_server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())