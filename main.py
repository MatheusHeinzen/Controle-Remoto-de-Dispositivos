import socket
import threading
import json
from datetime import datetime
import time

# --- Configurações Globais ---
HOST = '127.0.0.1'  # Endereço do servidor (localhost)
PORT = 5000         # Porta do servidor

# --- Dados do Sistema ---
DISPOSITIVOS = {}    # Dicionário global para armazenar dispositivos conectados
LOGS = []            # Lista para armazenar logs do sistema
lock = threading.Lock()  # Lock para acesso thread-safe aos dados globais

# --- Funções Utilitárias ---
def log(mensagem):
    """
    Adiciona uma mensagem ao log com timestamp e imprime no console.
    """
    hora = datetime.now().strftime("%H:%M:%S")
    LOGS.append(f"[{hora}] {mensagem}")
    print(f"[{hora}] {mensagem}")

def obter_lampada_por_nome(nome):
    """
    Retorna a instância da lâmpada pelo nome, se existir.
    """
    with lock:
        return DISPOSITIVOS.get(nome)

# --- Tratamento de Clientes ---
def tratar_cliente(conn, addr):
    """
    Função executada por thread para tratar comunicação com cada cliente.
    """
    log(f"Conexão estabelecida com {addr}")
    nome_dispositivo = None

    try:
        data = conn.recv(1024).decode('utf-8').strip()
        if not data:
            return
            
        mensagem = json.loads(data)
        
        if mensagem.get("tipo") == "REGISTRO":
            # Registro de novo dispositivo
            nome_dispositivo = mensagem.get("dispositivo")
            # Cria e registra a lâmpada no dicionário global
            with lock:
                if nome_dispositivo not in DISPOSITIVOS:
                    DISPOSITIVOS[nome_dispositivo] = Lampada(nome_dispositivo)
            # Confirma registro ao cliente
            resposta = {"tipo": "RESPOSTA", "status": "OK"}
            conn.sendall(json.dumps(resposta).encode('utf-8'))
        elif mensagem.get("tipo") == "COMANDO":
            # Recebe comando para dispositivo
            dispositivo_destino = mensagem.get("dispositivo")
            lampada = obter_lampada_por_nome(dispositivo_destino)
            resposta = processar_comando(lampada, mensagem)
            conn.sendall(json.dumps(resposta).encode('utf-8'))

        while True:
            data = conn.recv(1024)
            if not data:
                break

            try:
                mensagem = json.loads(data.decode('utf-8').strip())
                log(f"📩 {nome_dispositivo} -> {mensagem}")

                if mensagem.get("tipo") == "COMANDO":
                    dispositivo_destino = mensagem.get("dispositivo")
                    lampada = obter_lampada_por_nome(dispositivo_destino)
                    resposta = processar_comando(lampada, mensagem)
                    conn.sendall(json.dumps(resposta).encode('utf-8'))

            except json.JSONDecodeError:
                # Mensagem JSON inválida recebida
                erro = {"tipo": "ERRO", "mensagem": "JSON inválido"}
                conn.sendall(json.dumps(erro).encode('utf-8'))

    except Exception as e:
        log(f"❌ Erro em {addr}: {str(e)}")
    finally:
        # Remove dispositivo do dicionário ao desconectar
        if nome_dispositivo and nome_dispositivo in DISPOSITIVOS:
            with lock:
                del DISPOSITIVOS[nome_dispositivo]
        conn.close()
        log(f"⚠️ {nome_dispositivo} desconectado.")

def processar_comando(lampada, comando):
    """
    Processa comandos recebidos para uma lâmpada e retorna resposta.
    """
    acao = comando.get("dados")

    if acao == "LIGAR":
        lampada.estado = True
        return {
            "tipo": "RESPOSTA", 
            "dispositivo": lampada.nome, 
            "dados": "LIGADA", 
            "estado_atual": "LIGADA" if lampada.estado else "DESLIGADA",
            "status": "sucesso"
        }
    elif acao == "DESLIGAR":
        lampada.estado = False
        return {
            "tipo": "RESPOSTA", 
            "dispositivo": lampada.nome, 
            "dados": "DESLIGADA",
            "estado_atual": "LIGADA" if lampada.estado else "DESLIGADA",
            "status": "sucesso"
        }
    elif acao == "STATUS":
        return {
            "tipo": "RESPOSTA",
            "dispositivo": lampada.nome,
            "dados": "LIGADA" if lampada.estado else "DESLIGADA",
            "estado_atual": "LIGADA" if lampada.estado else "DESLIGADA",
            "status": "sucesso"
        }
    else:
        # Comando desconhecido
        return {
            "tipo": "ERRO",
            "dispositivo": lampada.nome,
            "mensagem": "Comando desconhecido"
        }

# --- Servidor Principal ---
def iniciar_servidor():
    """
    Inicializa o servidor TCP e aceita conexões de clientes.
    """
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
                log(f"🔵 Conexões ativas: {threading.active_count()}")

    except Exception as e:
        log(f"❌ Erro no servidor: {str(e)}")

# --- Cliente (Lâmpada) ---
class Lampada:
    """
    Classe que representa uma lâmpada/dispositivo.
    """
    def __init__(self, nome):
        self.nome = nome
        self.estado = False  # Estado inicial: desligada

    def conectar(self):
        """
        Conecta a lâmpada ao servidor e processa comandos recebidos.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((HOST, PORT))
                
                # Envia mensagem de registro ao servidor
                registro = {"tipo": "REGISTRO", "dispositivo": self.nome}
                s.sendall(json.dumps(registro).encode('utf-8'))
                
                data = s.recv(1024)
                if data:
                    resposta = json.loads(data.decode('utf-8'))
                    if resposta.get("status") == "OK":
                        print(f"💡 [{self.nome}] Registrada e pronta para comandos")

                while True:
                    data = s.recv(1024)
                    if not data:
                        break

                    try:
                        msg = json.loads(data.decode('utf-8').strip())
                        print(f"📥 [{self.nome}] Recebeu: {msg}")

                        # Processa o comando e atualiza estado
                        if msg.get("dados") == "LIGAR":
                            self.estado = True
                            resposta = {
                                "tipo": "RESPOSTA",
                                "dispositivo": self.nome,
                                "dados": "LIGADA",
                                "estado_atual": self.estado
                            }
                        elif msg.get("dados") == "DESLIGAR":
                            self.estado = False
                            resposta = {
                                "tipo": "RESPOSTA",
                                "dispositivo": self.nome,
                                "dados": "DESLIGADA",
                                "estado_atual": self.estado
                            }
                        elif msg.get("dados") == "STATUS":
                            resposta = {
                                "tipo": "RESPOSTA",
                                "dispositivo": self.nome,
                                "dados": "LIGADA" if self.estado else "DESLIGADA",
                                "estado_atual": self.estado
                            }
                        else:
                            # Comando desconhecido
                            resposta = {
                                "tipo": "ERRO",
                                "dispositivo": self.nome,
                                "dados": "COMANDO_DESCONHECIDO"
                            }

                        s.sendall(json.dumps(resposta).encode('utf-8'))
                        print(f"📤 [{self.nome}] Enviou: {resposta}")

                    except json.JSONDecodeError:
                        # Mensagem inválida recebida
                        erro = {"tipo": "ERRO", "dispositivo": self.nome, "dados": "MENSAGEM_INVALIDA"}
                        s.sendall(json.dumps(erro).encode('utf-8'))
                        print(f"❌ [{self.nome}] Mensagem inválida recebida")

        except Exception as e:
            print(f"❌ [{self.nome}] Erro: {str(e)}")

# --- Painel de Controle Interativo ---
def painel_interativo():
    """
    Painel de controle para enviar comandos aos dispositivos conectados.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.settimeout(5.0)

            while True:
                print("\n" + "="*50)
                print("PAINEL DE CONTROLE - DISPOSITIVOS CONECTADOS")
                print("="*50)
                
                # Lista dispositivos disponíveis
                with lock:
                    dispositivos_disponiveis = list(DISPOSITIVOS.keys())
                
                if not dispositivos_disponiveis:
                    print("Nenhum dispositivo conectado. Aguardando...")
                    time.sleep(2)
                    continue
                
                print("\nDispositivos disponíveis:")
                for i, dispositivo in enumerate(dispositivos_disponiveis, 1):
                    print(f"{i}. {dispositivo}")
                
                print("\nSelecione os dispositivos (ex: 1,3 ou 'all' para todos):")
                selecao = input(">> ").strip().lower()
                
                if selecao == "all":
                    dispositivos_selecionados = dispositivos_disponiveis
                else:
                    try:
                        indices = [int(i.strip())-1 for i in selecao.split(",")]
                        dispositivos_selecionados = [dispositivos_disponiveis[i] for i in indices if 0 <= i < len(dispositivos_disponiveis)]
                    except:
                        print("Seleção inválida!")
                        continue
                
                if not dispositivos_selecionados:
                    print("Nenhum dispositivo válido selecionado!")
                    continue
                
                print("\nComandos disponíveis:")
                print("1. LIGAR")
                print("2. DESLIGAR")
                print("3. STATUS")
                print("4. VOLTAR")
                
                opcao = input("Selecione o comando: ").strip()
                
                if opcao == "4":
                    continue
                
                comandos = { "1": "LIGAR", "2": "DESLIGAR", "3": "STATUS" }
                comando = comandos.get(opcao)
                
                if not comando:
                    print("Comando inválido!")
                    continue
                
                # Envia comandos para todos selecionados
                for dispositivo in dispositivos_selecionados:
                    msg = {
                        "tipo": "COMANDO",
                        "dispositivo": dispositivo,
                        "dados": comando,
                        "timestamp": str(time.time())
                    }
                    
                    try:
                        s.sendall(json.dumps(msg).encode('utf-8'))
                        print(f"\n➡️ Enviado {comando} para {dispositivo}")
                        
                        # Recebe resposta
                        data = s.recv(1024)
                        if data:
                            resposta = json.loads(data.decode('utf-8').strip())
                            print(f"📥 Resposta de {dispositivo}: {resposta}")
                        else:
                            print(f"⚠️ Sem resposta de {dispositivo}")
                            
                    except Exception as e:
                        print(f"❌ Erro ao comunicar com {dispositivo}: {str(e)}")
                
                input("\nPressione Enter para continuar...")

    except Exception as e:
        print(f"❌ Painel: Erro: {str(e)}")

# --- Main ---
if __name__ == "__main__":
    # Inicia servidor em thread separada
    servidor_thread = threading.Thread(target=iniciar_servidor)
    servidor_thread.daemon = True
    servidor_thread.start()
    time.sleep(1)

    # Inicia lâmpadas (simulação de 4 dispositivos)
    lampadas = [Lampada(f"LAMPADA_{i+1}") for i in range(4)]
    for lampada in lampadas:
        threading.Thread(target=lampada.conectar, daemon=True).start()
        time.sleep(0.5)

    # Aguarda conexões
    time.sleep(2)

    # Inicia painel interativo
    painel_interativo()

    # Mantém o programa rodando enquanto houver threads ativas
    while threading.active_count() > 1:
        time.sleep(1)