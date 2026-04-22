const landingPage = document.getElementById('landing-page');
const mainContainer = document.getElementById('main-container');
const editor = document.getElementById('editor');

let ws;
let myNickname = null;
let currentFile = 'Document1';

function enterEditor() {
    const nickname = document.getElementById('landing-nickname').value.trim();
    const port = document.getElementById('ws-port').value || 8080;

    if (!nickname) {
        alert('Digite um apelido!');
        return;
    }

    myNickname = nickname;

    ws = new WebSocket(`ws://localhost:${port}`);

    ws.onopen = () => {
        ws.send(JSON.stringify({
            action: 'set_nickname',
            nickname: myNickname
        }));
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'files_list') {
            landingPage.style.display = 'none';
            mainContainer.classList.add('active');
        }

        if (data.type === 'file_content') {
            editor.value = data.content;
        }
    };

    editor.addEventListener('input', () => {
        ws.send(JSON.stringify({
            type: 'text_update',
            filename: currentFile,
            content: editor.value
        }));
    });
}

function createNewFile() {
    const name = prompt("Nome do arquivo:");
    if (name) {
        ws.send(JSON.stringify({
            type: 'create_file',
            filename: name
        }));
    }
}