import socket
import json
import threading

class Dispositivo:
    def __init__(self, nome, tipo, host='127.0.0.1', port=5000):
        self.nome = nome
        self.tipo = tipo
        self.estado = False
        self.host = host
        self.port = port

    def conectar(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            
            # Registra no servidor
            registro = {
                "tipo": "REGISTRO",
                "dispositivo": self.nome,
                "dados": {"tipo": self.tipo}
            }
            s.sendall(json.dumps(registro).encode('utf-8'))

            # Thread para receber comandos
            threading.Thread(
                target=self.receber_comandos,
                args=(s,),
                daemon=True
            ).start()

            # Mantém a conexão ativa
            while True:
                pass

    def receber_comandos(self, conn):
        while True:
            try:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break

                comando = json.loads(data)
                print(f"📥 Comando recebido: {comando}")

                if comando["dados"] == "LIGAR":
                    self.estado = True
                    resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": "LIGADO"}
                elif comando["dados"] == "DESLIGAR":
                    self.estado = False
                    resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": "DESLIGADO"}
                elif comando["dados"] == "STATUS":
                    resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": "LIGADO" if self.estado else "DESLIGADO"}

                conn.sendall(json.dumps(resposta).encode('utf-8'))
            except:
                break

class Lampada(Dispositivo):
    def __init__(self, nome, host='127.0.0.1', port=5000):
        super().__init__(nome, "LAMPADA", host, port)

if __name__ == "__main__":
    nome = input("Nome do dispositivo (ex: LAMPADA_1): ")
    lampada = Lampada(nome)
    lampada.conectar()