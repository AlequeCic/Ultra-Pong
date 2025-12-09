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
    
    def host(self, port: int = 5555) -> bool:
        self.mode = 'host'
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
        self.mode = 'client'
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
