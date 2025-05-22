import asyncio
import json
from datetime import datetime

class ServidorAsync:
    def __init__(self):
        self.dispositivos = {}  # {nome: (reader, writer)}
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
                    nome_dispositivo = nome
                    self.log(f"✅ {nome} registrado.")

                elif tipo == "COMANDO":
                    dispositivo = mensagem["dispositivo"]
                    if dispositivo in self.dispositivos:
                        _, writer_disp = self.dispositivos[dispositivo]
                        writer_disp.write((json.dumps(mensagem) + "\n").encode('utf-8'))
                        await writer_disp.drain()

                        resp_data = await reader.readline()
                        if resp_data:
                            writer.write(resp_data)
                            await writer.drain()
                        self.log(f"📤 Comando enviado para {dispositivo}")
                    else:
                        erro = {"tipo": "ERRO", "dados": f"Dispositivo '{dispositivo}' não encontrado."}
                        writer.write((json.dumps(erro) + "\n").encode('utf-8'))
                        await writer.drain()

                elif tipo == "PING":
                    self.log(f"💓 PING recebido de {mensagem['dispositivo']}")

        except Exception as e:
            self.log(f"❌ Erro em {addr}: {e}")
        finally:
            if nome_dispositivo and nome_dispositivo in self.dispositivos:
                del self.dispositivos[nome_dispositivo]
                self.log(f"⚠️ {nome_dispositivo} removido.")
            writer.close()
            await writer.wait_closed()

    async def iniciar(self):
        server = await asyncio.start_server(
            self.tratar_cliente, '0.0.0.0', 5000
        )
        async with server:
            self.log("🖥️ Servidor assíncrono iniciado na porta 5000")
            await server.serve_forever()

if __name__ == "__main__":
    servidor = ServidorAsync()
    asyncio.run(servidor.iniciar())
