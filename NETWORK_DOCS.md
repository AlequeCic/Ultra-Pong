# Ultra-Pong - Implementação de Rede TCP

Documentação das mudanças para implementação de multiplayer via TCP.

---

## Arquivos Novos

### `network/client.py`
Cliente TCP para comunicação com o servidor.
- Conexão/desconexão com timeout
- Envio e recepção assíncrona (thread separada)
- Protocolo: 4 bytes de tamanho + payload JSON
- `TCP_NODELAY` para baixa latência

### `network/server.py`
Servidor TCP que aceita múltiplos clientes.
- Suporta até 2 jogadores simultâneos
- Broadcast de mensagens para todos os clientes
- Keep-alive para detectar desconexões
- Thread-safe com locks

### `network/network_handler.py`
Wrapper que abstrai cliente/servidor para o jogo.
- `host(port)` - Inicia servidor e aguarda oponente
- `join(ip, port)` - Conecta a um host existente
- Gerencia troca de inputs e estado do jogo

### `network/network_input.py`
InputHandler para jogador remoto.
- Substitui o InputHandler local para o oponente
- Obtém direção do movimento via rede

---

## Arquivos Modificados

### `main.py`
**Antes:** Apenas iniciava o jogo local.

**Depois:** Suporta argumentos de linha de comando:
```bash
python main.py                      # Jogo local
python main.py --host 5555          # Hospedar partida
python main.py --join <IP> 5555     # Conectar a partida
```

### `game.py`
**Antes:** `Game()` sem parâmetros.

**Depois:** `Game(game_mode, network)` - Recebe modo de jogo e handler de rede.

### `playingstate.py`
**Mudanças principais:**
1. Importa `NetworkHandler` e `NetworkInputHandler`
2. `enter()` aceita parâmetro `network`
3. `setup_players()` configura jogador remoto para multiplayer
4. `fixed_step()` processa mensagens de rede a cada frame
5. `_send_local_input()` envia input do jogador local
6. `_apply_game_state()` sincroniza bola e placar (com interpolação)

---

## Como Testar

**Terminal 1 (Host):**
```bash
cd Code
python main.py --host 5555
```

**Terminal 2 (Cliente):**
```bash
cd Code
python main.py --join <IP_DO_HOST> 5555
```

---

## Arquitetura de Rede

```
┌─────────────────────────────────────────────────────────┐
│                        HOST                              │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │  TCP Server  │◄──►│  Game Loop   │                   │
│  │  (porta 5555)│    │  + Física    │                   │
│  └──────────────┘    └──────────────┘                   │
│         ▲                                                │
└─────────│────────────────────────────────────────────────┘
          │ TCP
          ▼
┌─────────────────────────────────────────────────────────┐
│                       CLIENTE                            │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │  TCP Client  │◄──►│  Game Loop   │                   │
│  │              │    │  (renderiza) │                   │
│  └──────────────┘    └──────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

**Modelo:** Servidor autoritativo
- Host: Calcula física, envia estado
- Cliente: Envia inputs, recebe e renderiza estado
