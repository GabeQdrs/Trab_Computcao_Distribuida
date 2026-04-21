import tornado.ioloop
import tornado.web
import tornado.websocket

# Dicionário de salas
salas = {}

class ChatHandler(tornado.websocket.WebSocketHandler):

    def open(self):
        # Pega a sala da URL (?sala=abc)
        self.sala = self.get_argument("sala", "default")

        # Cria a sala se não existir
        if self.sala not in salas:
            salas[self.sala] = []

        # Adiciona cliente na sala
        salas[self.sala].append(self)

        print(f"Cliente conectado na sala {self.sala}")

        # Avisa os outros
        for cliente in salas[self.sala]:
            cliente.write_message("🔵 Um usuário entrou na sala")

    def on_message(self, message):
        print(f"[{self.sala}] {message}")

        # Envia mensagem só pra mesma sala
        for cliente in salas[self.sala]:
            cliente.write_message(message)

    def on_close(self):
        # Remove cliente da sala
        salas[self.sala].remove(self)

        print(f"Cliente saiu da sala {self.sala}")

        # Avisa os outros
        for cliente in salas[self.sala]:
            cliente.write_message("🔴 Um usuário saiu da sala")

    def check_origin(self, origin):
        # Libera conexão de qualquer origem (pra teste)
        return True


def make_app():
    return tornado.web.Application([
        (r"/", ChatHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    print("Servidor rodando em http://localhost:8888")
    tornado.ioloop.IOLoop.current().start()