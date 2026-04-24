// Estado da aplicação
let ws = null;
let myNickname = null;
let currentDocument = 'Document1';
let documents = ['Document1'];
let isLocalUpdate = false;
let renamingDoc = null;
let shouldReconnect = true;

// Elementos DOM
const landingPage = document.getElementById('landing-page');
const mainContainer = document.getElementById('main-container');
const editor = document.getElementById('editor');
const documentsList = document.getElementById('documents-list');
const statusMessage = document.getElementById('status-message');
const myNicknameSpan = document.getElementById('my-nickname');
const clientsCountSpan = document.getElementById('clients-count');

// ========== CONEXÃO ==========
function connectWebSocket() {
    shouldReconnect = true;
    const serverHost = window.location.hostname || 'localhost';
    const serverPort = 8080;
    ws = new WebSocket(`ws://${serverHost}:${serverPort}`);
    
    ws.onopen = () => {
        console.log('✅ Conectado ao servidor');
        updateStatus('Conectado ✓');
        
        ws.send(JSON.stringify({
            action: 'set_nickname',
            nickname: myNickname
        }));
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleMessage(data);
    };
    
    ws.onclose = () => {
        console.log('❌ Desconectado');
        updateStatus('Desconectado ✗ Tentando reconectar...');
        if (shouldReconnect) {
            setTimeout(connectWebSocket, 3000);
        }
    };
    
    ws.onerror = (error) => {
        console.error('Erro:', error);
        updateStatus('Erro na conexão');
    };
}

// ========== MANIPULAÇÃO DE MENSAGENS ==========
function handleMessage(data) {
    switch(data.type) {
        case 'error':
            alert(data.message);
            if (data.message.includes('Nickname já em uso')) {
                shouldReconnect = false;
                returnToLanding();
            }
            break;
            
        case 'documents_list':
            enterEditor(data.documents);
            break;
            
        case 'document_content':
            if (data.name === currentDocument && data.content !== editor.value) {
                isLocalUpdate = true;
                const cursorPos = editor.selectionStart;
                editor.value = data.content;
                editor.setSelectionRange(
                    Math.min(cursorPos, editor.value.length),
                    Math.min(cursorPos, editor.value.length)
                );
                isLocalUpdate = false;
            }
            if (data.edited_by && data.edited_by !== myNickname) {
                updateStatus(`✏️ ${data.edited_by} está editando...`);
            }
            break;
            
        case 'document_created':
            documents.push(data.name);
            renderDocumentsList();
            updateStatus(`📄 ${data.created_by} criou: ${data.name}`);
            break;
            
        case 'document_deleted':
            documents = documents.filter(d => d !== data.name);
            renderDocumentsList();
            if (currentDocument === data.name) {
                selectDocument(documents[0] || 'Document1');
            }
            updateStatus(`🗑️ ${data.deleted_by} deletou: ${data.name}`);
            break;
            
        case 'document_renamed':
            documents = documents.map(d => d === data.old_name ? data.new_name : d);
            if (currentDocument === data.old_name) {
                currentDocument = data.new_name;
            }
            renderDocumentsList();
            updateStatus(`✏️ ${data.renamed_by} renomeou para: ${data.new_name}`);
            break;
            
        case 'client_joined':
            clientsCountSpan.textContent = data.total;
            if (data.nickname !== myNickname) {
                updateStatus(`✅ ${data.nickname} entrou`);
            }
            break;
            
        case 'client_left':
            clientsCountSpan.textContent = data.total;
            updateStatus(`❌ ${data.nickname} saiu`);
            break;
    }
}

// ========== INTERFACE ==========
function enterEditor(docs) {
    documents = docs;
    landingPage.style.display = 'none';
    mainContainer.classList.add('active');
    myNicknameSpan.textContent = myNickname;
    
    renderDocumentsList();
    if (documents.length > 0) {
        selectDocument(documents[0]);
    }
}

function selectDocument(name) {
    currentDocument = name;
    editor.value = '';
    editor.placeholder = `Carregando ${name}...`;
    renderDocumentsList();
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'get_document',
            name: name
        }));
    }
}

function renderDocumentsList() {
    documentsList.innerHTML = '';
    
    documents.forEach(doc => {
        const item = document.createElement('div');
        item.className = `doc-item ${doc === currentDocument ? 'active' : ''} ${renamingDoc === doc ? 'renaming' : ''}`;
        
        if (renamingDoc === doc) {
            item.innerHTML = `
                <input type="text" class="doc-input" 
                    onkeypress="if(event.key==='Enter') finishRename('${doc}')" 
                    onblur="finishRename('${doc}')">
            `;
        } else {
            item.innerHTML = `
                <div class="doc-name" ondblclick="startRename('${doc}')">${doc}</div>
                <div class="doc-actions">
                    <button class="doc-action-btn" onclick="renameDocument('${doc}')" title="Renomear">✏️</button>
                    <button class="doc-action-btn delete" onclick="deleteDocument('${doc}')" title="Deletar">🗑️</button>
                </div>
            `;
        }
        
        item.onclick = (e) => {
            if (!e.target.classList.contains('doc-action-btn') && 
                !e.target.classList.contains('doc-input')) {
                selectDocument(doc);
            }
        };
        
        documentsList.appendChild(item);
    });
    
    setTimeout(() => {
        const input = document.querySelector('.doc-input');
        if (input) {
            input.focus();
            input.select();
        }
    }, 50);
}

// ========== AÇÕES DOS DOCUMENTOS ==========
function createDocument() {
    const name = prompt('Nome do novo documento:');
    if (name && name.trim()) {
        ws.send(JSON.stringify({
            type: 'create_document',
            name: name.trim()
        }));
    }
}

function deleteDocument(name) {
    if (confirm(`Deletar "${name}"?`)) {
        ws.send(JSON.stringify({
            type: 'delete_document',
            name: name
        }));
    }
}

function renameDocument(name) {
    startRename(name);
}

function startRename(name) {
    renamingDoc = name;
    renderDocumentsList();
}

function finishRename(oldName) {
    const input = document.querySelector('.doc-input');
    const newName = input?.value.trim();
    
    if (newName && newName !== oldName) {
        ws.send(JSON.stringify({
            type: 'rename_document',
            old_name: oldName,
            new_name: newName
        }));
    }
    
    renamingDoc = null;
    renderDocumentsList();
}

// ========== UTILITÁRIOS ==========
function updateStatus(message) {
    statusMessage.textContent = message;
    setTimeout(() => {
        if (statusMessage.textContent === message) {
            statusMessage.textContent = 'Conectado ✓';
        }
    }, 4000);
}

function returnToLanding() {
    // Resetar estado
    ws = null;
    myNickname = null;
    currentDocument = 'Document1';
    documents = ['Document1'];
    isLocalUpdate = false;
    renamingDoc = null;
    
    // Voltar à landing page
    landingPage.style.display = 'block';
    mainContainer.classList.remove('active');
    
    // Focar no input
    const input = document.getElementById('landing-nickname');
    input.focus();
    input.select();
}

// ========== EVENTOS ==========
editor.addEventListener('input', () => {
    if (!isLocalUpdate && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'update_document',
            name: currentDocument,
            content: editor.value
        }));
    }
});

function enterApp() {
    const input = document.getElementById('landing-nickname');
    const nickname = input.value.trim();
    
    if (!nickname) {
        alert('Digite um apelido!');
        return;
    }
    
    myNickname = nickname;
    connectWebSocket();
}

document.getElementById('landing-nickname').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') enterApp();
});

document.getElementById('landing-nickname').focus();