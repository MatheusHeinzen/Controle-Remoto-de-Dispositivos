# Projeto 3: Controle Remoto de Dispositivos

## Descrição

Este projeto implementa um sistema de controle remoto de dispositivos (ex: lâmpadas) via comunicação TCP, utilizando threads e sockets em Python.  
O sistema é composto por três partes principais:

- **Servidor:** Centraliza a comunicação, recebe comandos do painel e encaminha para os dispositivos, mantendo o estado de cada um.
- **Dispositivos (Lâmpadas):** Clientes que se registram no servidor, recebem comandos (`LIGAR`, `DESLIGAR`, `STATUS`) e respondem com seu estado atual.
- **Painel de Controle:** Interface interativa no terminal que permite ao usuário enviar comandos para um ou mais dispositivos e visualizar as respostas.

## Como Funciona

- O servidor é iniciado em uma thread separada e aguarda conexões de dispositivos e do painel.
- Cada lâmpada é instanciada em sua própria thread, conecta ao servidor e aguarda comandos.
- O painel de controle permite selecionar dispositivos conectados e enviar comandos, exibindo as respostas em tempo real.
- Toda a comunicação é feita via JSON sobre TCP.

## Requisitos Atendidos

- **Comandos:** Suporte aos comandos `LIGAR`, `DESLIGAR` e `STATUS`.
- **Resposta dos clientes:** Cada dispositivo executa o comando e responde com seu estado atual (`LIGADA` ou `DESLIGADA`).
- **Log:** O painel exibe todos os comandos enviados e as respostas recebidas.
- **Arquitetura:** Cliente-servidor, com múltiplos dispositivos e painel interativo.

## Estrutura dos Arquivos

- `main.py` — Código principal do servidor, painel e dispositivos.
- `README.md` — Este arquivo de documentação.

## Como Executar

1. **Requisitos:** Python 3.8+ (sem dependências externas).
2. **Execução:**  
   No terminal, execute:
   ```bash
   python main.py
   ```
   O script inicia automaticamente o servidor, quatro lâmpadas e o painel interativo.

3. **Fluxo:**
   - O servidor inicia e aguarda conexões.
   - As lâmpadas se registram e ficam aguardando comandos.
   - O painel permite selecionar dispositivos e enviar comandos, exibindo as respostas.

## Exemplo de Uso

```
🖥️ Servidor iniciado em 127.0.0.1:5000. Aguardando conexões...
💡 [LAMPADA_1] Registrada e pronta para comandos
...
PAINEL DE CONTROLE - DISPOSITIVOS CONECTADOS
Dispositivos disponíveis:
1. LAMPADA_1
2. LAMPADA_2
...
➡️ Enviado LIGAR para LAMPADA_1
📥 Resposta de LAMPADA_1: {'tipo': 'RESPOSTA', 'dispositivo': 'LAMPADA_1', 'dados': 'LIGADA', ...}
```

## Observações

- O código é multi-threaded e suporta múltiplos dispositivos simultâneos.
- O painel pode ser facilmente adaptado para interface gráfica ou web.
- O servidor mantém o estado de cada dispositivo e faz o roteamento correto dos comandos.
- Comentários feitos via CHATGPT para documentação.

---

**Atende integralmente ao pedido do professor:**
- Comandos e respostas implementados.
- Log no painel.
- Arquitetura cliente-servidor robusta e extensível.