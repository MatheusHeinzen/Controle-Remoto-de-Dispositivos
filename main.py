import socket
import threading
import json
from datetime import datetime

# --- Configurações Globais ---
HOST = '127.0.0.1'  # Escuta em todos os IPs
PORT = 5000       # Porta do servidor

# --- Dados do Sistema ---
DISPOSITIVOS = {}  # Dicionário para armazenar conexões dos dispositivos
LOGS = []          # Logs do sistema

# --- Funções Utilitárias ---
def log(mensagem):
    hora = datetime.now().strftime("%H:%M:%S")
    LOGS.append(f"[{hora}] {mensagem}")
    print(f"[{hora}] {mensagem}")

# --- Tratamento de Clientes ---
def tratar_cliente(conn, addr):
    log(f"Conexão estabelecida com {addr}")
    nome_dispositivo = None

    try:
        # Recebe o registro do dispositivo
        data = conn.recv(1024).decode('utf-8').strip()
        mensagem = json.loads(data)
        
        if mensagem.get("tipo") == "REGISTRO":
            nome_dispositivo = mensagem["dispositivo"]
            DISPOSITIVOS[nome_dispositivo] = conn
            log(f"✅ {nome_dispositivo} registrado (IP: {addr[0]})")

        # Loop para receber comandos
        while True:
            data = conn.recv(1024)
            if not data:
                break

            mensagem = json.loads(data.decode('utf-8').strip())
            log(f"📩 {nome_dispositivo} -> {mensagem}")

            if mensagem.get("tipo") == "COMANDO":
                dispositivo_alvo = mensagem["dispositivo"]
                if dispositivo_alvo in DISPOSITIVOS:
                    DISPOSITIVOS[dispositivo_alvo].sendall(data)
                    log(f"📤 Comando enviado para {dispositivo_alvo}")
                else:
                    erro = {"tipo": "ERRO", "dados": f"Dispositivo '{dispositivo_alvo}' não encontrado."}
                    conn.sendall(json.dumps(erro).encode('utf-8'))

    except Exception as e:
        log(f"❌ Erro em {addr}: {e}")
    finally:
        if nome_dispositivo and nome_dispositivo in DISPOSITIVOS:
            del DISPOSITIVOS[nome_dispositivo]
        conn.close()
        log(f"⚠️ {nome_dispositivo} desconectado.")

# --- Servidor Principal ---
def iniciar_servidor():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        log(f"🖥️ Servidor iniciado em {HOST}:{PORT}. Aguardando conexões...")

        while True:
            conn, addr = s.accept()
            thread = threading.Thread(target=tratar_cliente, args=(conn, addr))
            thread.start()
            log(f"🔵 Conexões ativas: {threading.active_count() - 1}")

# --- Cliente (Lâmpada) ---
class Lampada:
    def __init__(self, nome):
        self.nome = nome
        self.estado = False

    def conectar(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                
                # Registra a lâmpada no servidor
                registro = {"tipo": "REGISTRO", "dispositivo": self.nome}
                s.sendall(json.dumps(registro).encode('utf-8'))
                print(f"💡 [{self.nome}] Conectada e aguardando comandos...")

                while True:
                    data = s.recv(1024)
                    if not data:
                        break

                    comando = json.loads(data.decode('utf-8').strip())
                    print(f"📥 [{self.nome}] Recebeu: {comando}")

                    # Processa o comando
                    if comando["dados"] == "LIGAR":
                        self.estado = True
                        resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": "LIGADA"}
                    elif comando["dados"] == "DESLIGAR":
                        self.estado = False
                        resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": "DESLIGADA"}
                    elif comando["dados"] == "STATUS":
                        resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": "LIGADA" if self.estado else "DESLIGADA"}
                    else:
                        resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": "COMANDO_DESCONHECIDO"}

                    s.sendall(json.dumps(resposta).encode('utf-8'))

        except Exception as e:
            print(f"❌ [{self.nome}] Erro: {e}")

# --- Painel de Controle ---
def painel_controle():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            dispositivos = ["LAMPADA_1", "LAMPADA_2", "LAMPADA_3", "LAMPADA_4"]
            comandos = ["LIGAR", "STATUS", "DESLIGAR", "STATUS"]

            for dispositivo in dispositivos:
                print(f"\n🔘 Painel: Controlando {dispositivo}")
                for comando in comandos:
                    msg = {"tipo": "COMANDO", "dispositivo": dispositivo, "dados": comando}
                    s.sendall(json.dumps(msg).encode('utf-8'))
                    print(f"➡️ Enviado: {comando} para {dispositivo}")

                    resposta = s.recv(1024).decode('utf-8').strip()
                    print(f"📥 Resposta: {resposta}")

    except Exception as e:
        print(f"❌ Painel: Erro: {e}")

# --- Main ---
if __name__ == "__main__":
    import time

    # Inicia o servidor em uma thread separada
    servidor_thread = threading.Thread(target=iniciar_servidor, daemon=True)
    servidor_thread.start()
    time.sleep(1)  # Espera o servidor iniciar

    # Inicia as lâmpadas (cada uma em uma thread)
    lampadas = [Lampada(f"LAMPADA_{i+1}") for i in range(4)]
    for lampada in lampadas:
        threading.Thread(target=lampada.conectar, daemon=True).start()
        time.sleep(0.5)

    # Inicia o painel de controle
    painel_controle()