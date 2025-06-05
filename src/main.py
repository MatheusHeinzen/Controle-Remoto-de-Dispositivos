import asyncio
import json
import threading
import time
import socket
from datetime import datetime

### ------------------ SERVIDOR ------------------

class ServidorAsync:
    def __init__(self):
        self.dispositivos = {}
        self.queues = {}
        self.logs = []

    def log(self, mensagem):
        hora = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{hora}] {mensagem}")
        print(f"[{hora}] {mensagem}")

    async def tratar_cliente(self, reader, writer):
        addr = writer.get_extra_info('peername')
        nome_dispositivo = None
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                mensagem = json.loads(data.decode('utf-8').strip())
                self.log(f"📩 {addr} -> {mensagem}")

                tipo = mensagem.get("tipo")

                if tipo == "REGISTRO":
                    nome = mensagem["dispositivo"]
                    self.dispositivos[nome] = (reader, writer)
                    self.queues[nome] = asyncio.Queue()
                    nome_dispositivo = nome
                    self.log(f"✅ {nome} registrado.")

                elif tipo == "COMANDO":
                    dispositivo = mensagem["dispositivo"]
                    if dispositivo in self.dispositivos:
                        _, writer_disp = self.dispositivos[dispositivo]
                        writer_disp.write((json.dumps(mensagem) + "\n").encode('utf-8'))
                        await writer_disp.drain()

                        try:
                            resposta = await asyncio.wait_for(self.queues[dispositivo].get(), timeout=10)
                            writer.write((json.dumps(resposta) + "\n").encode('utf-8'))
                            await writer.drain()
                        except asyncio.TimeoutError:
                            erro = {"tipo": "ERRO", "dados": f"Sem resposta do dispositivo '{dispositivo}'."}
                            writer.write((json.dumps(erro) + "\n").encode('utf-8'))
                            await writer.drain()
                        self.log(f"📤 Comando enviado para {dispositivo}")
                    else:
                        erro = {"tipo": "ERRO", "dados": f"Dispositivo '{dispositivo}' não encontrado."}
                        writer.write((json.dumps(erro) + "\n").encode('utf-8'))
                        await writer.drain()

                elif tipo == "RESPOSTA":
                    if nome_dispositivo and nome_dispositivo in self.queues:
                        await self.queues[nome_dispositivo].put(mensagem)

                elif tipo == "PING":
                    self.log(f"💓 PING recebido de {mensagem['dispositivo']}")

        except Exception as e:
            self.log(f"❌ Erro em {addr}: {e}")
        finally:
            if nome_dispositivo and nome_dispositivo in self.dispositivos:
                del self.dispositivos[nome_dispositivo]
            if nome_dispositivo and nome_dispositivo in self.queues:
                del self.queues[nome_dispositivo]
            self.log(f"⚠️ {nome_dispositivo} removido.")
            writer.close()
            await writer.wait_closed()

    async def iniciar(self):
        # Cria um socket TCP explícito
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', 5000))
        sock.listen()
        sock.setblocking(False)  # Modo não-bloqueante para asyncio

        self.log("🖥️ Servidor assíncrono iniciado na porta 5000")

        # Cria o servidor asyncio usando o socket existente
        server = await asyncio.start_server(
            self.tratar_cliente,
            sock=sock  # Passa o socket já criado
        )

        async with server:
            await server.serve_forever()


def rodar_servidor():
    servidor = ServidorAsync()
    asyncio.run(servidor.iniciar())

### ------------------ PAINEL ------------------

async def painel_comandos():
    # Cria um socket TCP explícito
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)  # Modo não-bloqueante para asyncio

    # Conecta usando asyncio
    await asyncio.get_event_loop().sock_connect(sock, ('127.0.0.1', 5000))

    # Cria reader/writer a partir do socket
    reader, writer = await asyncio.open_connection(sock=sock)

    dispositivos = ["LAMPADA_1", "LAMPADA_2", "LAMPADA_3", "LAMPADA_4"]
    comandos = ["LIGAR", "STATUS", "DESLIGAR", "STATUS"]

    for dispositivo in dispositivos:
        print(f"\n🟦 Painel: Enviando comandos para {dispositivo}")
        for comando in comandos:
            print(f"➡️ Painel: Enviando '{comando}' para {dispositivo}")
            msg = {
                "tipo": "COMANDO",
                "dispositivo": dispositivo,
                "dados": comando
            }
            try:
                writer.write((json.dumps(msg) + "\n").encode('utf-8'))
                await writer.drain()
            except ConnectionResetError:
                print(f"❌ Conexão com o servidor foi encerrada.")
                return

            try:
                data = await asyncio.wait_for(reader.readline(), timeout=10)
                if data:
                    resposta = json.loads(data.decode('utf-8').strip())
                    print(f"📥 Painel recebeu de {dispositivo}: {resposta}")
                else:
                    print(f"⚠️ Sem resposta do dispositivo {dispositivo}.")
                    break
            except asyncio.TimeoutError:
                print(f"⏳ Tempo de resposta esgotado para {dispositivo}.")
            except ConnectionResetError:
                print(f"❌ Conexão com o servidor foi encerrada.")
                return
            await asyncio.sleep(1)

    print("🔒 Painel encerrando conexão.")
    writer.close()
    await writer.wait_closed()

def rodar_painel():
    asyncio.run(painel_comandos())

### ------------------ LÂMPADA ------------------

class LampadaAsync:
    def __init__(self, nome):
        self.nome = nome
        self.estado = False

    async def conectar(self):
        # Cria um socket TCP explícito
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)  # Modo não-bloqueante para asyncio

        # Conecta usando asyncio
        await asyncio.get_event_loop().sock_connect(sock, ('127.0.0.1', 5000))

        # Cria reader/writer a partir do socket
        reader, writer = await asyncio.open_connection(sock=sock)

        registro = {
            "tipo": "REGISTRO",
            "dispositivo": self.nome,
            "dados": {"tipo": "LAMPADA"}
        }
        writer.write((json.dumps(registro) + "\n").encode('utf-8'))
        await writer.drain()

        print(f"💡 [{self.nome}] conectada e aguardando comandos...")

        while True:
            try:
                data = await asyncio.wait_for(reader.readline(), timeout=60)
                if not data:
                    print(f"⚠️ [{self.nome}] Conexão encerrada.")
                    break

                comando = json.loads(data.decode('utf-8').strip())
                print(f"📥 [{self.nome}] recebeu: {comando}")

                if comando["dados"] == "LIGAR":
                    self.estado = True
                    resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": "LIGADA"}
                    print(f"💡 [{self.nome}] foi LIGADA")
                elif comando["dados"] == "DESLIGAR":
                    self.estado = False
                    resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": "DESLIGADA"}
                    print(f"💡 [{self.nome}] foi DESLIGADA")
                elif comando["dados"] == "STATUS":
                    estado_str = "LIGADA" if self.estado else "DESLIGADA"
                    resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": estado_str}
                    print(f"💡 [{self.nome}] STATUS: {estado_str}")
                else:
                    resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": "COMANDO DESCONHECIDO"}
                    print(f"❓ [{self.nome}] Comando desconhecido recebido.")

                writer.write((json.dumps(resposta) + "\n").encode('utf-8'))
                await writer.drain()

            except asyncio.TimeoutError:
                print(f"⏳ [{self.nome}] aguardando comandos...")
            except Exception as e:
                print(f"❌ [{self.nome}] Erro: {e}")
                break

def rodar_lampada(nome):
    lampada = LampadaAsync(nome)
    asyncio.run(lampada.conectar())

### ------------------ MAIN ------------------

if __name__ == "__main__":
    # Thread do Servidor
    t_servidor = threading.Thread(target=rodar_servidor, daemon=True)
    t_servidor.start()

    time.sleep(1)  # Espera servidor iniciar

    # Threads das Lâmpadas
    nomes_lampadas = ["LAMPADA_1", "LAMPADA_2", "LAMPADA_3", "LAMPADA_4"]
    threads_lampadas = []
    for nome in nomes_lampadas:
        t = threading.Thread(target=rodar_lampada, args=(nome,), daemon=True)
        t.start()
        threads_lampadas.append(t)
        time.sleep(0.5)  # Pequeno delay para registro sequencial

    time.sleep(1)

    # Thread do Painel
    t_painel = threading.Thread(target=rodar_painel)
    t_painel.start()

    t_painel.join()  # Aguarda painel terminar
    print("✅ Teste concluído.")
