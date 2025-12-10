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

O protocolo utiliza **JSON** dentro de um fluxo **TCP** com framing.

Formato base:

```json
{
  "type": "<tipo_da_mensagem>",
  "payload": { ... }
}
````

---

## 2.1. Framing (Separação de Mensagens)

Cada envio segue:

```
4 bytes → tamanho da mensagem JSON
N bytes → conteúdo JSON serializado
```

Isso evita problemas de "pacotes colados" ou incompletos no TCP.

---

## 2.2. Mensagens Cliente → Servidor

### **input**

```json
{
  "type": "input",
  "direction": -1 | 0 | 1
}
```

### **pause_request**

```json
{
  "type": "pause_request",
  "paused": true/false
}
```

---

## 2.3. Mensagens Servidor → Cliente

### **welcome**

```json
{
  "type": "welcome",
  "player_id": 1
}
```

### **assign_player**

```json
{
  "type": "assign_player",
  "player_id": 2
}
```

### **game_start**

Indica que ambos estão sincronizados para iniciar.

---

### **game_state**

Snapshot completo do host:

```json
{
  "type": "game_state",
  "ball_x": ...,
  "ball_y": ...,
  "ball_dx": ...,
  "ball_dy": ...,
  "ball_speed": ...,
  "score_t1": ...,
  "score_t2": ...,
  "phase": "...",
  "tick": ...,
  "countdown_end": ...
}
```

---

### **opponent_input**

```json
{
  "type": "opponent_input",
  "direction": -1 | 0 | 1
}
```

---

### **pause_state**

```json
{
  "type": "pause_state",
  "paused": true/false,
  "initiator": "host" | "client"
}
```

---

### **client_disconnected**

```json
{
  "type": "client_disconnected"
}
```

---

# 3. Mecânicas Internas do Jogo

## 3.1. Física da Bola

A bola possui:

* aceleração progressiva
* colisão angular dependendo da posição da raquete
* trilha visual dinâmica
* reinício com countdown sincronizado

---

## 3.2. Jogadores e Raquetes

As raquetes possuem:

* aceleração gradual
* atrito exponencial
* sistema de *charge shot*
* limites verticais de movimentação

---

## 3.3. Interpolação no Cliente

Para suavizar discrepâncias entre snapshots:

```
posição_final = lerp(posição_atual, posição_recebida, fator)
```

Isso suaviza saltos devido à latência.

---

# 4. Requisitos Mínimos

## Para Host

* Python 3.10+
* Porta TCP liberada (ex.: 5555)
* Firewall permitindo entrada

## Para Cliente

* Python 3.10+
* Biblioteca Pygame (`pip install pygame`)
* Acesso ao IP público ou local do host

---

# 5. Como Executar

## 🟦 Executar como Host

```
python main.py
→ Multiplayer Mode
→ Host Game
```

## 🟩 Executar como Cliente

```
python main.py
→ Multiplayer Mode
→ Join Game
→ Digitar IP e Porta do Host
```

---

# 6. Estrutura do Projeto

```
/
├── game.py
├── gamestate.py
├── playingstate.py
├── player.py
├── world.py
├── settings.py
├── states/
│   ├── mainmenustate.py
│   ├── optionsstate.py
│   ├── joinstate.py
│   ├── waitingstate.py
│   ├── multiplayerstate.py
├── network/
│   ├── server.py
│   ├── client.py
│   ├── network_handler.py
│   ├── network_input.py
└── assets/
```

---

# 7. Considerações Finais

Ultra Pong demonstra:

* arquitetura modular e organizada
* implementação prática do modelo cliente-servidor
* protocolo próprio sobre TCP
* sincronização consistente do gameplay
* manipulação real de latência
* menus, estados e experiência completa de jogo

O projeto cumpre totalmente os objetivos da disciplina **Redes de Computadores I**, servindo como referência sólida para estudos de aplicações distribuídas.

```




