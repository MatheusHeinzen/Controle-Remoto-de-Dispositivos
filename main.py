import socket
import threading
import json
from datetime import datetime
import time

# --- Configurações Globais ---
HOST = '127.0.0.1'
PORT = 5000

# --- Dados do Sistema ---
DISPOSITIVOS = {}
LOGS = []
lock = threading.Lock()

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
        #Recebe registro do dispositivo
        data = conn.recv(1024).decode('utf-8').strip()
        if not data:
            return
            
        mensagem = json.loads(data)
        
        if mensagem.get("tipo") == "REGISTRO":
            with lock:
                nome_dispositivo = mensagem["dispositivo"]
                DISPOSITIVOS[nome_dispositivo] = conn
                log(f"✅ {nome_dispositivo} registrado (IP: {addr[0]})")
                conn.sendall(json.dumps({"tipo": "CONFIRMACAO", "status": "OK"}).encode('utf-8'))

        #Loop principal para receber comandos
        while True:
            data = conn.recv(1024)
            if not data:
                break

            try:
                mensagem = json.loads(data.decode('utf-8').strip())
                if nome_dispositivo == None:
                    nome_dispositivo = "Painel"
                    log(f"📩 {nome_dispositivo} -> {mensagem}")
                else:
                    log(f"📩 {nome_dispositivo} -> {mensagem}")

                if mensagem.get("tipo") == "COMANDO":
                    dispositivo_alvo = mensagem["dispositivo"]
                    if dispositivo_alvo in DISPOSITIVOS:
                        DISPOSITIVOS[dispositivo_alvo].sendall(data)
                        log(f"📤 Comando enviado para {dispositivo_alvo}")
                    else:
                        erro = {"tipo": "ERRO", "mensagem": "Dispositivo não encontrado"}
                        conn.sendall(json.dumps(erro).encode('utf-8'))

            except json.JSONDecodeError:
                erro = {"tipo": "ERRO", "mensagem": "JSON inválido"}
                conn.sendall(json.dumps(erro).encode('utf-8'))

    except Exception as e:
        log(f"❌ Erro em {addr}: {str(e)}")
    finally:
        if nome_dispositivo and nome_dispositivo in DISPOSITIVOS:
            with lock:
                del DISPOSITIVOS[nome_dispositivo]
        conn.close()
        log(f"⚠️ {nome_dispositivo} desconectado.")

# --- Servidor Principal ---
def iniciar_servidor():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen(5)
            log(f"🖥️ Servidor iniciado em {HOST}:{PORT}. Aguardando conexões...")

            while True:
                conn, addr = s.accept()
                thread = threading.Thread(target=tratar_cliente, args=(conn, addr))
                thread.daemon = True
                thread.start()
                log(f"🔵 Conexões ativas: {threading.active_count() - 1}")

    except Exception as e:
        log(f"❌ Erro no servidor: {str(e)}")

# --- Lâmpada ---
class Lampada:
    def __init__(self, nome):
        self.nome = nome
        self.estado = False

    def conectar(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                
                #Registra a lâmpada
                registro = {"tipo": "REGISTRO", "dispositivo": self.nome}
                s.sendall(json.dumps(registro).encode('utf-8'))
                
                #Aguarda confirmação
                data = s.recv(1024)
                if data:
                    resposta = json.loads(data.decode('utf-8'))
                    if resposta.get("status") == "OK":
                        print(f"💡 [{self.nome}] Registrada e pronta para comandos")

                #Loop principal
                while True:
                    data = s.recv(1024)
                    if not data:
                        break

                    try:
                        msg = json.loads(data.decode('utf-8').strip())
                        print(f"📥 [{self.nome}] Recebeu: {msg}")

                        if msg.get("dados") == "LIGAR":
                            self.estado = True
                            resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": "LIGADA"}
                        elif msg.get("dados") == "DESLIGAR":
                            self.estado = False
                            resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": "DESLIGADA"}
                        elif msg.get("dados") == "STATUS":
                            resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": "LIGADA" if self.estado else "DESLIGADA"}
                        else:
                            resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": "COMANDO_DESCONHECIDO"}

                        s.sendall(json.dumps(resposta).encode('utf-8'))

                    except json.JSONDecodeError:
                        print(f"❌ [{self.nome}] Mensagem inválida")

        except Exception as e:
            print(f"❌ [{self.nome}] Erro: {str(e)}")

# --- Painel de Controle ---
def painel_controle():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            
            #Adiciona timeout para evitar bloqueio
            s.settimeout(5.0)
            
            dispositivos = ["LAMPADA_1", "LAMPADA_2", "LAMPADA_3", "LAMPADA_4"]
            comandos = ["LIGAR", "STATUS", "DESLIGAR", "STATUS"]

            for dispositivo in dispositivos:
                print(f"\n🔘 Painel: Controlando {dispositivo}")
                for comando in comandos:
                    msg = {
                        "tipo": "COMANDO", 
                        "dispositivo": dispositivo, 
                        "dados": comando,
                        "id": str(time.time())  #ID único para cada comando
                    }
                    
                    #Envia comando
                    s.sendall(json.dumps(msg).encode('utf-8'))
                    print(f"➡️ Enviado: {comando} para {dispositivo}")
                    
                    try:
                        #Aguarda
                        data = s.recv(1024)
                        if data:
                            resposta = json.loads(data.decode('utf-8').strip())
                            print(f"📥 Resposta: {resposta}")
                        else:
                            print("⚠️ Conexão fechada pelo servidor")
                            break
                            
                    except socket.timeout:
                        print("⏰ Timeout aguardando resposta")
                        continue
                    
    except Exception as e:
        print(f"❌ Painel: Erro: {str(e)}")

# --- Main ---
if __name__ == "__main__":
    #Inicia o servidor
    servidor_thread = threading.Thread(target=iniciar_servidor)
    servidor_thread.daemon = True
    servidor_thread.start()
    time.sleep(1)

    #Inicia as lâmpadas
    lampadas = [Lampada(f"LAMPADA_{i+1}") for i in range(4)]
    for lampada in lampadas:
        threading.Thread(target=lampada.conectar, daemon=True).start()
        time.sleep(0.5)

    #Aguarda tudo conectar
    time.sleep(1)

    painel_controle()

    while threading.active_count() > 1:
        time.sleep(1)