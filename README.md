# 🏓 Ultra Pong — Aplicação Distribuída Cliente/Servidor  
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue" />
  <img src="https://img.shields.io/badge/Pygame-2.x-green" />
  <img src="https://img.shields.io/badge/Socket-TCP-orange" />
  <img src="https://img.shields.io/badge/Arquitetura-Cliente%2FServidor-purple" />
  <img src="https://img.shields.io/badge/Disciplina-Redes%20de%20Computadores%20I-0055A4" />
</p>

---

# 1. Documentação do Software

## 1.1. Descrição Geral

**Ultra Pong** é um jogo multiplayer desenvolvido em Python utilizando **Pygame** e comunicação em rede via **TCP**.  
É composto por uma arquitetura cliente-servidor que demonstra princípios essenciais do funcionamento de aplicações distribuídas.

O software possui:

- **Modo Local (1x1):** dois jogadores usando o mesmo teclado  
- **Modo Multiplayer (1x1):** um jogador atua como *host*, o outro como *client*

Principais características:

- física customizada da bola  
- interpolação no cliente para suavizar a jogabilidade  
- sistema de pausa sincronizada  
- detecção imediata de desconexão  
- menus interativos baseados em máquina de estados  
- protocolo próprio de mensagens em JSON

---

## 1.2. Propósito do Software

O Ultra Pong foi criado com o intuito de:

- demonstrar, na prática, o funcionamento de uma aplicação distribuída  
- implementar um protocolo de aplicação baseado em JSON  
- compreender controle de conexão, troca de mensagens e sincronização  
- organizar um jogo completo com camadas bem separadas:
  - interface  
  - rede  
  - gameplay  
  - estados  
  - física  

Assim, o projeto serve tanto como jogo quanto como estudo de redes.

---

## 1.3. Motivação para Uso do Protocolo TCP

O TCP foi escolhido como camada de transporte por motivos essenciais:

### ✔ Confiabilidade  
Toda jogada depende de integridade do estado.  
Um pacote perdido poderia quebrar:

- posição da bola  
- pontuação  
- countdown  
- sincronização das fases

O TCP garante que **cada mensagem chega completa**.

### ✔ Ordenação  
A sequência das mensagens importa.  
Inputs e snapshots devem chegar exatamente na ordem em que foram enviados.

### ✔ Estabilidade  
Em um jogo como Pong, a prioridade é consistência e não velocidade extrema.  
A latência adicional do TCP é insignificante.

---

## 1.4. Arquitetura Geral do Sistema

O Ultra Pong é organizado em cinco camadas principais:

---

### 🎨 1) Interface e Menus (Frontend)

Responsáveis pela navegação do usuário:

- `MainMenuState`
- `MultiplayerModeState`
- `MultiplayerHostJoinState`
- `JoinState`
- `WaitingForPlayersState`
- `OptionsState`

Cada tela é um estado independente.

---

### 🔄 2) Máquina de Estados (State Machine)

Controlada pelos arquivos:

- `game.py`
- `gamestate.py`

A máquina de estados gerencia:

- fluxo das telas  
- entrada do gameplay  
- retorno ao menu  
- atualização e desenho em cada estado  

---

### 🧠 3) Gameplay e Física

Arquivos:

- `playingstate.py`
- `player.py`
- `world.py`

Responsáveis por:

- física da bola  
- colisões  
- movimentação das raquetes  
- placar  
- countdown  
- efeitos visuais da bola  
- lógica de pausa e desconexão  

---

### 🌐 4) Camada de Rede (TCP)

Arquivos:

- `server.py`  
- `client.py`  
- `network_handler.py`  
- `network_input.py`

Funções principais:

- framing de mensagens (tamanho + JSON)  
- controle de conexão  
- envio de inputs  
- envio de snapshots de estado  
- detecção de desconexão  
- gerenciamento do host e do cliente  

---

### ⚙️ 5) Configurações Globais

Em `settings.py`, contendo:

- dimensões de tela  
- FPS  
- cores  
- velocidades  
- tamanhos dos objetos  

---

## 1.5. Funcionamento Geral do Jogo

### Fluxo de jogo no modo multiplayer:

```

Main Menu
→ Multiplayer Mode
→ Host ou Join
→ (Host) cria servidor
→ (Client) insere IP e Porta
→ Tela de Espera
→ Ambos conectados
→ PlayingState (partida inicia)

````

### Papéis:

#### 🟦 Host
- simula física da bola  
- calcula colisões  
- controla pontuação  
- envia snapshots constantes  

#### 🟩 Cliente
- envia apenas direção da raquete  
- recebe estados do host  
- interpola a bola para suavizar latência  

---

# 2. Protocolo da Camada de Aplicação

O Ultra Pong utiliza um protocolo simples baseado em JSON enviado via TCP.  
Cada mensagem segue o formato:

    {
      "type": "<tipo>",
      "payload": { ... }
    }

Para evitar mensagens coladas no fluxo TCP, cada envio começa com 4 bytes indicando o tamanho do JSON.

As principais mensagens são:

### Cliente → Servidor
- **input**: envia direção da raquete (`-1`, `0`, `1`)
- **pause_request**: solicita pausa ou despausa

### Servidor → Cliente
- **welcome / assign_player**: identifica cada jogador
- **game_start**: início da partida
- **game_state**: snapshot contendo posição da bola, placar e estado do jogo
- **opponent_input**: repassa direção do oponente
- **pause_state**: sincroniza pausa
- **client_disconnected**: finaliza o jogo se alguém cair

Esse conjunto de mensagens é suficiente para sincronizar o jogo entre host e cliente.

---

# 3. Requisitos Mínimos

## Para Host

* Python 3.10+
* Porta TCP liberada (ex.: 5555)
* Firewall permitindo entrada

## Para Cliente

* Python 3.10+
* Biblioteca Pygame (`pip install pygame`)
* Acesso ao IP público ou local do host

---

# 4. Como Executar

Siga os passos abaixo para executar o Ultra Pong pela primeira vez:

### 1. Acesse a pasta do projeto
```
cd Ultra-Pong
```
### 2. Crie um ambiente virtual
```
python -m venv venv
```
### 🔹 3. Ative o ambiente virtual

#### ✔ Windows
```
venv\Scripts\activate
```
#### ✔ macOS / Linux
```
source venv/bin/activate
```
### 🔹 4. Instale as dependências necessárias
```
pip install pygame-ce
```
### 🔹 5. Acesse a pasta onde está o código do jogo
```
cd code
```
### 🔹 6. Execute o jogo
#### Windows
```
python main.py
```
#### macOS / Linux
```
python3 main.py
```

### 🟢 Pronto!
O Ultra Pong abrirá com o menu principal e você poderá escolher:
- Jogar localmente  
- Ser o Host  
- Entrar como Cliente  

## 🟦 Executar como Host

```
→ Multiplayer Mode
→ Host Game
```

## 🟩 Executar como Cliente

```
→ Multiplayer Mode
→ Join Game
→ Digitar IP e Porta do Host
```

---

# 5. Estrutura do Projeto

```
Ultra-Pong/
├── Code/
│ ├── Assets/
│ │ ├── MUSIC/
│ │ ├── SFX/
│ │ └── last_goal.mp3
│ │
│ ├── menu_state/
│ │ ├── joinstate.py
│ │ ├── multiplayerstate.py
│ │ ├── optionsstate.py
│ │ ├── pause.py
│ │ ├── ui.py
│ │ └── waitingstate.py
│ │
│ ├── network/
│ │ ├── client.py
│ │ ├── network_handler.py
│ │ ├── network_input.py
│ │ ├── server.py
│ │ ├── audio_manager.py
│ │ ├── networksync.py
│ │ └── init.py
│ │
│ ├── game.py
│ ├── gamestate.py
│ ├── inputhandler.py
│ ├── main.py
│ ├── menustate.py
│ ├── player.py
│ ├── playingstate.py
│ ├── settings.py
│ └── world.py
│
├── docs/
│ └── NETWORK_DOCUMENTATION.md
│
└── venv/
```




