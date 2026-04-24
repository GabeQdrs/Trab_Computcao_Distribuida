import asyncio, json, websockets, threading, http.server, socketserver, os
from datetime import datetime

# Configurações
DATA_FILE = 'documents.json'
WS_PORT = 8080
HTTP_PORT = 8000

# Estado global
documents = {}
connected_clients = {}  # {websocket: nickname}
active_nicknames = set()

def load_documents():
    """Carrega documentos do arquivo de persistência."""
    global documents
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            print(f"✅ Documentos carregados: {len(documents)} arquivos")
        except Exception as e:
            print(f"❌ Erro ao carregar: {e}")
            documents = {"Document1": ""}
    else:
        documents = {"Document1": ""}
    
    save_documents()

def save_documents():
    """Salva documentos no arquivo de persistência."""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(documents, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")

async def broadcast(message, exclude=None):
    """Envia mensagem para todos os clientes."""
    disconnected = []
    for client in connected_clients:
        if client == exclude:
            continue
        try:
            await client.send(message)
        except:
            disconnected.append(client)
    
    for client in disconnected:
        if client in connected_clients:
            nickname = connected_clients[client]
            del connected_clients[client]
            active_nicknames.discard(nickname.lower())

async def handle_connection(websocket):
    """Gerencia conexão WebSocket."""
    nickname = None
    
    try:
        async for message in websocket:
            data = json.loads(message)
            
            # 1. Configurar nickname
            if data.get("action") == "set_nickname":
                nickname = data["nickname"].strip()
                
                if nickname.lower() in active_nicknames:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Nickname já em uso!"
                    }))
                    await websocket.close()
                    return
                
                connected_clients[websocket] = nickname
                active_nicknames.add(nickname.lower())
                
                print(f"📥 Cliente conectado: {nickname}")
                
                # Notificar entrada
                await broadcast(json.dumps({
                    "type": "client_joined",
                    "nickname": nickname,
                    "total": len(connected_clients)
                }))
                
                # Enviar lista de documentos
                await websocket.send(json.dumps({
                    "type": "documents_list",
                    "documents": list(documents.keys())
                }))
                
                # Enviar documento atual
                await websocket.send(json.dumps({
                    "type": "document_content",
                    "name": "Document1",
                    "content": documents.get("Document1", "")
                }))
            
            # 2. Obter documento
            elif data.get("type") == "get_document":
                doc_name = data.get("name", "Document1")
                if doc_name in documents:
                    await websocket.send(json.dumps({
                        "type": "document_content",
                        "name": doc_name,
                        "content": documents[doc_name]
                    }))
            
            # 3. Atualizar documento
            elif data.get("type") == "update_document":
                doc_name = data.get("name", "Document1")
                if doc_name in documents:
                    documents[doc_name] = data["content"]
                    save_documents()
                    
                    await broadcast(json.dumps({
                        "type": "document_content",
                        "name": doc_name,
                        "content": documents[doc_name],
                        "edited_by": nickname
                    }), exclude=websocket)
            
            # 4. Criar documento
            elif data.get("type") == "create_document":
                doc_name = data.get("name")
                if doc_name and doc_name not in documents:
                    documents[doc_name] = ""
                    save_documents()
                    
                    await broadcast(json.dumps({
                        "type": "document_created",
                        "name": doc_name,
                        "created_by": nickname
                    }))
            
            # 4. Deletar documento
            elif data.get("type") == "delete_document":
                doc_name = data.get("name")
                if doc_name in documents:
                    del documents[doc_name]
                    
                    if len(documents) == 0:
                        documents["Document1"] = ""
                    
                    save_documents()
                    
                    await broadcast(json.dumps({
                        "type": "document_deleted",
                        "name": doc_name,
                        "deleted_by": nickname
                    }))
            
            # 5. Renomear documento
            elif data.get("type") == "rename_document":
                old_name = data.get("old_name")
                new_name = data.get("new_name")
                
                if old_name in documents and new_name and new_name not in documents:
                    documents[new_name] = documents.pop(old_name)
                    save_documents()
                    
                    await broadcast(json.dumps({
                        "type": "document_renamed",
                        "old_name": old_name,
                        "new_name": new_name,
                        "renamed_by": nickname
                    }))
    
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if websocket in connected_clients:
            nickname = connected_clients[websocket]
            del connected_clients[websocket]
            active_nicknames.discard(nickname.lower())
            
            await broadcast(json.dumps({
                "type": "client_left",
                "nickname": nickname,
                "total": len(connected_clients)
            }))
            print(f"📤 Cliente desconectado: {nickname}")

def start_http_server():
    """Inicia servidor HTTP para arquivos estáticos."""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", HTTP_PORT), handler) as httpd:
        print(f"🌐 HTTP Server: http://localhost:{HTTP_PORT}")
        httpd.serve_forever()

async def main():
    load_documents()
    
    # Iniciar WebSocket em todas as interfaces de rede para permitir conexão entre PCs
    ws_server = await websockets.serve(handle_connection, "0.0.0.0", WS_PORT)
    print(f"🔌 WebSocket Server: ws://0.0.0.0:{WS_PORT}")
    
    # Iniciar HTTP em thread separada
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    
    print(f"\n✨ Servidor rodando!")
    print(f"   📄 Documentos: {len(documents)}")
    print(f"   👥 Clientes: {len(connected_clients)}")
    print("\n✓ Pressione Ctrl+C para parar\n")
    
    await ws_server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())