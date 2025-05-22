import asyncio
import json

class LampadaAsync:
    def __init__(self, nome):
        self.nome = nome
        self.estado = False

    async def conectar(self):
        reader, writer = await asyncio.open_connection('127.0.0.1', 5000)

        registro = {
            "tipo": "REGISTRO",
            "dispositivo": self.nome,
            "dados": {"tipo": "LAMPADA"}
        }
        writer.write((json.dumps(registro) + "\n").encode('utf-8'))
        await writer.drain()

        print(f"🔗 {self.nome} conectada e aguardando comandos...")

        while True:
            try:
                data = await asyncio.wait_for(reader.readline(), timeout=30)  # ⏱️ timeout de 30s
                if not data:
                    print("⚠️ Conexão encerrada.")
                    break

                comando = json.loads(data.decode('utf-8').strip())
                print(f"📥 {self.nome} recebeu: {comando}")

                if comando["dados"] == "LIGAR":
                    self.estado = True
                    resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": "LIGADA"}
                elif comando["dados"] == "DESLIGAR":
                    self.estado = False
                    resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": "DESLIGADA"}
                elif comando["dados"] == "STATUS":
                    resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": "LIGADA" if self.estado else "DESLIGADA"}
                else:
                    resposta = {"tipo": "RESPOSTA", "dispositivo": self.nome, "dados": "COMANDO DESCONHECIDO"}

                writer.write((json.dumps(resposta) + "\n").encode('utf-8'))
                await writer.drain()

            except asyncio.TimeoutError:
                print("⏳ Nenhum comando recebido. Mantendo a conexão ativa...")
                continue  # Continua o loop mesmo sem dados

            except Exception as e:
                print(f"❌ Erro: {e}")
                break

async def main():
    nome = input("Nome do dispositivo (ex: LAMPADA_1): ")
    lampada = LampadaAsync(nome)
    await lampada.conectar()

if __name__ == "__main__":
    asyncio.run(main())
