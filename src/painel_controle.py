import socket
import json

class PainelControle:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port

    def enviar_comando(self, dispositivo, comando):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                mensagem = {
                    "tipo": "COMANDO",
                    "dispositivo": dispositivo,
                    "dados": comando
                }
                s.sendall(json.dumps(mensagem).encode('utf-8'))
                print(f"📤 Comando enviado para {dispositivo}: {comando}")
                #Espera resposta
                resposta = s.recv(1024).decode('utf-8')
                if resposta:
                    resposta_json = json.loads(resposta)
                    print(f"🔔 Resposta de {resposta_json['dispositivo']}: {resposta_json['dados']}")
                else:
                    print("❌ Nenhuma resposta recebida.")
        except Exception as e:
            print(f"❌ Erro ao enviar comando: {e}")

    def menu_interativo(self):
        while True:
            print("\n🛠️ PAINEL DE CONTROLE")
            print("Comandos: LIGAR, DESLIGAR, STATUS")
            print("Digite 'SAIR' para fechar.\n")
            dispositivo = input("Dispositivo: ").strip()
            if dispositivo.upper() == "SAIR":
                break  # Sai do loop
            comando = input("Comando (LIGAR/DESLIGAR/STATUS): ").strip().upper()
            if comando not in ["LIGAR", "DESLIGAR", "STATUS"]:
                print("❌ Comando inválido! Use LIGAR, DESLIGAR ou STATUS")
                continue
            self.enviar_comando(dispositivo, comando)
        print("Painel encerrado.") 

if __name__ == "__main__":
    painel = PainelControle()
    painel.menu_interativo()