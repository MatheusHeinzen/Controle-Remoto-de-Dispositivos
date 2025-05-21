import socket
import threading
import json
from datetime import datetime

class Servidor:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.dispositivos = {}
        self.logs = []
        self.lock = threading.Lock()

    def log(self, mensagem):
        hora = datetime.now().strftime("%H:%M:%S")
        with self.lock:
            self.logs.append(f"[{hora}] {mensagem}")
            print(f"[{hora}] {mensagem}")  #Mostra no console

    def iniciar(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen()
            self.log(f"🖥️ Servidor iniciado em {self.host}:{self.port}")

            while True:
                conn, addr = s.accept()
                threading.Thread(
                    target=self.tratar_cliente,
                    args=(conn, addr),
                    daemon=True
                ).start()

    def tratar_cliente(self, conn, addr):
        try:
            while True:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break

                mensagem = json.loads(data)
                self.log(f"📩 {addr} -> {mensagem}")

                if mensagem["tipo"] == "REGISTRO":
                    nome = mensagem["dispositivo"]
                    with self.lock:
                        self.dispositivos[nome] = conn
                    self.log(f"✅ {nome} registrado.")

                elif mensagem["tipo"] == "RESPOSTA":
                    #Resposta do Dispositivo
                    self.log(f"📤 {mensagem['dispositivo']} respondeu: {mensagem['dados']}")

                elif mensagem["tipo"] == "COMANDO":
                    dispositivo = mensagem["dispositivo"]
                    if dispositivo in self.dispositivos:
                        self.dispositivos[dispositivo].sendall(json.dumps(mensagem).encode('utf-8'))
                        self.log(f"📤 Comando enviado para {dispositivo}: {mensagem['dados']}")

        except Exception as e:
            self.log(f"❌ Erro em {addr}: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    servidor = Servidor()
    servidor.iniciar()