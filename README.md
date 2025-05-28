# Projeto 3: Controle Remoto de Dispositivos

## Descrição

Este projeto implementa um sistema de controle remoto de dispositivos (ex: lâmpadas) via comunicação TCP assíncrona.  
Um **servidor** central recebe conexões de dispositivos (clientes) e de um **painel** especial, que envia comandos e exibe logs das respostas.

- **Servidor:** Encaminha comandos do painel para os dispositivos e repassa as respostas.
- **Dispositivos (clientes):** Executam comandos recebidos (ligar, desligar, status) e respondem com seu estado atual.
- **Painel:** Interface especial que envia comandos para os dispositivos e exibe logs de comandos e respostas.

## Requisitos Atendidos

- **Comandos:** O sistema suporta os comandos `ligar`, `desligar` e `status`.
- **Resposta dos clientes:** Cada dispositivo executa o comando recebido e responde com seu estado atual (`LIGADA` ou `DESLIGADA`).
- **Log:** O painel exibe na tela todos os comandos enviados e as respostas recebidas dos dispositivos.
- **Arquitetura:** Comunicação assíncrona entre servidor, painel e múltiplos dispositivos.

## Estrutura dos Arquivos

- `src/main.py` — Código principal do servidor, painel e dispositivos.
- `README.md` — Este arquivo de documentação.

## Como Executar

1. **Requisitos:** Python 3.8+ (recomenda-se 3.11+), sem dependências externas.
2. **Execução:**  
   Basta rodar o arquivo `main.py`:
   ```bash
   python src/main.py
   ```
   O script inicia o servidor, registra 4 lâmpadas e executa o painel automaticamente em threads separadas.

3. **Fluxo:**
   - O servidor inicia e aguarda conexões.
   - Cada lâmpada se conecta, se registra e aguarda comandos.
   - O painel conecta, envia comandos sequenciais para cada lâmpada e exibe as respostas.
   - Todos os logs são impressos no terminal.

## Exemplo de Saída

```
🖥️ Servidor assíncrono iniciado na porta 5000
✅ LAMPADA_1 registrado.
...
🟦 Painel: Enviando comandos para LAMPADA_1
➡️ Painel: Enviando 'LIGAR' para LAMPADA_1
📥 Painel recebeu de LAMPADA_1: {'tipo': 'RESPOSTA', 'dispositivo': 'LAMPADA_1', 'dados': 'LIGADA'}
...
```

## Observações

- O código é totalmente assíncrono e suporta múltiplos dispositivos.
- O painel pode ser adaptado para interface gráfica ou web, se desejado.
- O servidor faz o roteamento correto das mensagens e mantém logs detalhados.

---

**Atende integralmente ao pedido do professor:**
- Comandos e respostas implementados.
- Log no painel.
- Arquitetura cliente-servidor robusta e extensível.