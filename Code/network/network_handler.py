from network.client import TCPClient
from network.server import TCPServer


class NetworkHandler:
    def __init__(self, mode: str = 'client'):
        self.mode = mode
        self.client: TCPClient | None = None
        self.server: TCPServer | None = None
        self.player_id: int = 0
        self.opponent_direction: float = 0.0
        self.game_state: dict = {}
        self.connected = False
        self.waiting_for_opponent = False
        self.opponent_disconnected = False  # NEW: Track if opponent left during game
        # pause sync
        self.remote_pause_state = False
        self.pause_initiator = ""  # "local" or "remote"
        self.pause_received = False  # Flag to know when we received a pause state
    
    def host(self, port: int = 5555) -> bool:
        # Ensure previous sockets/threads are closed before re-hosting
        self.disconnect()

        self.mode = 'host'
        self.connected = False
        self.waiting_for_opponent = False
        self.opponent_disconnected = False
        self.game_state = {}
        self.opponent_direction = 0.0
        self.remote_pause_state = False
        self.pause_initiator = ""
        self.pause_received = False
        self.server = TCPServer('0.0.0.0', port, max_clients=2)

        if not self.server.start():
            return False

        self.client = TCPClient('localhost', port)
        if not self.client.connect():
            self.server.stop()
            return False
        
        self.player_id = 1
        self.waiting_for_opponent = True
        self.connected = True
        return True
    
    def join(self, host: str, port: int = 5555) -> bool:
        # Ensure previous sockets/threads are closed before joining again
        self.disconnect()

        self.mode = 'client'
        self.connected = False
        self.waiting_for_opponent = False
        self.opponent_disconnected = False
        self.game_state = {}
        self.opponent_direction = 0.0
        self.remote_pause_state = False
        self.pause_initiator = ""
        self.pause_received = False
        self.client = TCPClient(host, port)
        
        if not self.client.connect():
            return False
        
        self.waiting_for_opponent = True
        self.connected = True
        return True
    
    def update(self):
        if self.server:
            self._process_server_messages()
        
        if self.client:
            self._process_client_messages()
            # Check if client lost connection to host
            if not self.client.is_connected and self.connected:
                self.opponent_disconnected = True
                self.connected = False
    
    def _process_server_messages(self):
        if not self.server:
            return
        
        for msg in self.server.get_messages():
            msg_type = msg.get('type')
            
            if msg_type == 'client_connected':
                if self.server.get_client_count() == 2:
                    self.waiting_for_opponent = False
                    self.server.send_to_client(msg['client_id'], {
                        'type': 'assign_player',
                        'player_id': 2
                    })
                    self.server.send_to_all({'type': 'game_start'})
            
            elif msg_type == 'client_disconnected':
                self.waiting_for_opponent = True
                self.opponent_disconnected = True  # Opponent left during game

            elif msg_type == 'pause_request':
                # Cliente pediu para pausar/despausar - broadcast para todos
                paused = msg.get('paused', True)
                client_id = msg.get('_client_id')
                initiator_for_host = "local" if client_id == self.player_id else "remote"
                
                self.remote_pause_state = paused
                self.pause_initiator = initiator_for_host
                self.pause_received = True

                # Envia para todos exceto quem pediu
                # Para outros clientes, sempre é "remote" (veio de um oponente)
                self.server.send_to_all_except(client_id, {
                    'type': 'pause_state',
                    'paused': paused,
                    'initiator': 'remote'
                })
            
            elif msg_type == 'input':
                client_id = msg.get('_client_id')
                if client_id != self.player_id:
                    self.opponent_direction = msg.get('direction', 0)
    
    def _process_client_messages(self):
        if not self.client:
            return
        
        for msg in self.client.get_messages():
            msg_type = msg.get('type')
            
            if msg_type == 'welcome':
                if self.mode != 'host':
                    self.player_id = msg.get('your_id', 0)
            
            elif msg_type == 'assign_player':
                self.player_id = msg.get('player_id', 0)
            
            elif msg_type == 'game_start':
                self.waiting_for_opponent = False
            
            elif msg_type == 'game_state':
                self.game_state = msg
            
            elif msg_type == 'opponent_input':
                self.opponent_direction = msg.get('direction', 0)

            elif msg_type == 'pause_state':
                # Recebeu estado de pausa do host
                self.remote_pause_state = msg.get('paused', False)
                self.pause_initiator = msg.get('initiator', 'remote')
                self.pause_received = True
    
    def send_input(self, direction: float):
        if self.client:
            self.client.send({'type': 'input', 'direction': direction})
        
        if self.server:
            self.server.send_to_all_except(self.player_id, {
                'type': 'opponent_input',
                'direction': direction
            })
    
    def send_game_state(self, state: dict):
        if self.server:
            state['type'] = 'game_state'
            self.server.send_to_all(state)
    
    def get_opponent_direction(self) -> float:
        return self.opponent_direction
    
    def get_game_state(self) -> dict:
        return self.game_state
    
    def is_host(self) -> bool:
        return self.mode == 'host'
    
    def is_ready(self) -> bool:
        return self.connected and not self.waiting_for_opponent
    
    def is_opponent_connected(self) -> bool:
        """Returns True if opponent is still connected during gameplay"""
        return self.connected and not self.opponent_disconnected

    def disconnect(self):
        if self.client:
            self.client.disconnect()
            self.client = None
        
        if self.server:
            self.server.stop()
            self.server = None
        
        self.connected = False

    def send_pause_request(self, paused: bool):
        """Envia requisição de pausa"""
        if self.client:
            # Cliente envia requisição para o host
            self.client.send({
                'type': 'pause_request', 
                'paused': paused
            })
        elif self.server and self.is_host():
            # Host pausa diretamente e notifica todos
            self.remote_pause_state = paused
            self.pause_initiator = "local"
            self.pause_received = True
            # Envia para todos os clientes
            self.server.send_to_all({
                'type': 'pause_state',
                'paused': paused,
                'initiator': 'remote'
            })

    def get_pause_state(self):
        """Retorna o estado de pausa recebido e reseta a flag"""
        if self.pause_received:
            self.pause_received = False
            return self.remote_pause_state, self.pause_initiator
        return None, ""
