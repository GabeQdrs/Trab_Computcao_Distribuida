// Pega a sala da URL (?sala=abc)
const params = new URLSearchParams(window.location.search);
const sala = params.get("sala") || "default";

// Conecta no servidor
const ws = new WebSocket(`ws://localhost:8888?sala=${sala}`);

// Quando conectar
ws.onopen = () => {
  console.log("Conectado na sala:", sala);
};

// Receber mensagens
ws.onmessage = (event) => {
  const chat = document.getElementById("chat");
  const novaMsg = document.createElement("p");
  novaMsg.textContent = event.data;
  chat.appendChild(novaMsg);
};

// Enviar mensagem
function enviarMensagem() {
  const input = document.getElementById("mensagem");
  const mensagem = input.value;

  if (mensagem.trim() !== "") {
    ws.send(mensagem);
    input.value = "";
  }
}