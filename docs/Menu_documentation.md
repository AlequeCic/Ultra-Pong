# 🎮 Ultra Pong – Menu System

Sistema de menus desenvolvido para o projeto **Ultra Pong (Redes de Computadores)**, oferecendo toda a navegação necessária para jogar localmente ou em multiplayer usando sockets TCP.

---

## 📌 Visão Geral

O menu foi estruturado em forma de **máquina de estados**, onde cada tela é uma classe independente.  
A navegação entre elas é controlada pelo `state_manager`.

O sistema inclui:

- **Main Menu**
- **Multiplayer Mode Selection**
- **Host / Join Selection**
- **Join Screen (IP/Port)**
- **Options Menu**
- **Waiting Room**

---

## 🧩 Estrutura dos Menus

### **1. Main Menu**
Arquivo: `menustate.py`  
Funções:
- Start Game
- Multiplayer
- Options
- Quit

Layout inspirado no estilo clássico “pong”, com:
- Linha central pontilhada  
- Paddles decorativos  
- Painel central  
- Destaque animado na opção selecionada

---

### **2. Multiplayer Mode (1v1 / 2v2)**
Arquivo: `multiplayerstate.py`  

Nesta tela o jogador escolhe o tipo de partida:
- **1 vs 1** → Avança para Host/Join  
- **2 vs 2** → Exibe mensagem “coming soon”  
- **Back**

Inclui:
- Título
- Barra inferior decorativa
- Feedback visual das opções

---

### **3. Host or Join**
Arquivo: `multiplayerstate.py`  

Após escolher o modo, o jogador define:
- **Host match** (cria servidor e aguarda cliente)
- **Join match** (vai para tela de IP)
- **Back**

Usa `NetworkHandler` para iniciar servidor ou preparar conexão.

---

### **4. Join Screen (IP e Porta)**
Arquivo: `joinstate.py`  

Tela para digitar:
- Endereço IP
- Porta

Recursos:
- Campo ativo com cursor piscando  
- `TAB` alterna entre IP/Port  
- `ENTER` tenta conectar  
- Mostra erros (“Invalid port”, “Connection failed”)

---

### **5. Options Menu**
Arquivo: `optionsstate.py`  

Configurações ajustáveis:
- Velocidade da bola  
- Velocidade do jogador  
- Countdown inicial  

Cada item possui:
- Label  
- Lista de valores possíveis  
- Atualização automática das variáveis globais do jogo

Navegação:
- ↑↓ trocar item  
- ←→ mudar valor  
- ENTER / ESC voltar  

---

### **6. Waiting Room**
Arquivo: `waitingstate.py`  

Tela exibida enquanto:
- O host aguarda um cliente  
- Um cliente tenta se conectar ao host  

Recursos:
- Texto animado com “...”  
- Exibe IP e porta quando host  
- Mostra tempo de espera  
- Cancela com `ESC`

Ao detectar que ambos estão conectados, avança para o estado **PLAYING**.

---

## ⌨️ Controles Gerais do Menu

| Ação | Teclas |
|------|--------|
| Navegar | ↑ ↓ / W S |
| Selecionar | ENTER / SPACE |
| Voltar | ESC |
| Alterar valores | ← → / A D |
| Alternar campo (Join) | TAB |

---

## 🧠 Arquitetura do Sistema

Cada tela é uma classe que herda de `BaseState`, implementando os métodos:
- `enter()`  
- `handle_events()`  
- `update()`  
- `draw()`  
- `exit()`

A troca entre telas é feita através de:
```python
self.state_manager.change_state(StateID.NAME)

---

## 🌐 Multiplayer (Resumo Técnico)

Toda a parte de rede usa `NetworkHandler`:

- `host(5555)` → cria servidor  
- `join(ip, port)` → tenta conectar  
- `update()` → processa mensagens  
- `is_ready()` → verifica se ambos os jogadores sincronizaram  

O menu apenas gerencia o fluxo e as transições de tela, sem lidar com lógica de jogo.

