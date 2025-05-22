import asyncio
import json

async def painel():
    reader, writer = await asyncio.open_connection('127.0.0.1', 5000)

    print("⚙️ PAINEL DE CONTROLE ASSÍNCRONO")
    print("Comandos: LIGAR, DESLIGAR, STATUS")
    print("Digite 'SAIR' para fechar.")

    dispositivo = input("Dispositivo: ").strip()

    while True:
        comando = input("Comando: ").strip().upper()

        if comando == "SAIR":
            print("🔒 Encerrando painel...")
            break

        msg = {
            "tipo": "COMANDO",
            "dispositivo": dispositivo,
            "dados": comando
        }

        writer.write((json.dumps(msg) + "\n").encode('utf-8'))
        await writer.drain()

        try:
            data = await asyncio.wait_for(reader.readline(), timeout=20)
            if not data:
                print("⚠️ Sem resposta, talvez o dispositivo tenha desconectado.")
                break
            resposta = json.loads(data.decode('utf-8').strip())
            print(f"📥 Resposta: {resposta}")
        except asyncio.TimeoutError:
            print("⏳ Tempo de resposta esgotado.")

    writer.close()
    await writer.wait_closed()

if __name__ == "__main__":
    asyncio.run(painel())
