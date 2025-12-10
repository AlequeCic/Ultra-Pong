from network.network_handler import NetworkHandler
from network.network_input import NetworkInputHandler
import math


class NetworkSync:
    """Gerencia sincronização de estado de jogo pela rede"""
    
    def __init__(self, network, ball, world, players):
        self.network = network
        self.ball = ball
        self.world = world
        self.players = players
    
    def send_local_input(self):
        """Envia input do jogador local e estado do jogo (host)"""
        if not self.network:
            return
        
        is_host = self.network.is_host()
        
        # Enviar input do jogador local + posição Y do paddle
        local_player_key = 'player1' if self.network.player_id == 1 else 'player2'
        if local_player_key in self.players:
            player = self.players[local_player_key]
            if hasattr(player.input_handler, 'get_direction'):
                direction = player.input_handler.get_direction()
                paddle_y = player.rect.centery  # Captura posição Y atual
                self.network.send_input(direction, paddle_y=paddle_y)
        
        # Host aplica posição do oponente recebida via input
        if is_host:
            self._apply_opponent_position_from_input()
            self.send_game_state(is_host)
        
        # Cliente aplica estado recebido
        if not is_host:
            self.apply_game_state()
    
    def send_game_state(self, is_host):
        """Host envia estado do jogo para clientes"""
        if not is_host or not self.network or not self.ball or not self.world:
            return
        
        # Captura posições dos paddles
        p1_y = None
        p2_y = None
        if 'player1' in self.players:
            p1_y = self.players['player1'].rect.centery
        if 'player2' in self.players:
            p2_y = self.players['player2'].rect.centery
        
        game_state = {
            'ball_x': self.ball.rect.centerx,
            'ball_y': self.ball.rect.centery,
            'ball_dx': self.ball.direction.x,
            'ball_dy': self.ball.direction.y,
            'ball_speed': self.ball.speed,
            'score_t1': self.world.score['TEAM_1'],
            'score_t2': self.world.score['TEAM_2'],
            'phase': self.world.phase,
            'tick': self.world.tick,
            'countdown_end': self.world.countdownEndTick,
            'p1_y': p1_y,  # Posição Y do player 1
            'p2_y': p2_y   # Posição Y do player 2
        }
    
        self.network.send_game_state(game_state)
    
    def apply_game_state(self):
        """Cliente aplica estado recebido do host"""
        if not self.network or not self.ball or not self.world:
            return
        
        state = self.network.get_game_state()
        if not state:
            return
        
        # Interpolação suave da bola
        if 'ball_x' in state:
            lerp = 0.4
            target_x = state['ball_x']
            target_y = state['ball_y']
            self.ball.rect.centerx += (target_x - self.ball.rect.centerx) * lerp
            self.ball.rect.centery += (target_y - self.ball.rect.centery) * lerp
            self.ball.direction.x = state['ball_dx']
            self.ball.direction.y = state['ball_dy']
            self.ball.speed = state['ball_speed']
        
        # Atualiza pontuação
        if 'score_t1' in state:
            self.world.score['TEAM_1'] = state['score_t1']
            self.world.score['TEAM_2'] = state['score_t2']
        
        # Atualiza estado do jogo
        if 'phase' in state:
            self.world.phase = state['phase']
            self.world.tick = state.get('tick', self.world.tick)
            self.world.countdownEndTick = state.get('countdown_end')
        
        # Aplica posição do oponente (player1 para o cliente que é player2)
        # O cliente é player2, então o oponente é player1
        if 'p1_y' in state and state['p1_y'] is not None:
            if 'player1' in self.players:
                opponent = self.players['player1']
                target_y = state['p1_y']
                # Interpolação suave para evitar teleporte
                lerp_paddle = 0.5
                opponent.rect.centery += (target_y - opponent.rect.centery) * lerp_paddle
    
    def _apply_opponent_position_from_input(self):
        """Host aplica posição do oponente recebida via mensagem de input"""
        if not self.network:
            return
        
        opponent_pos = self.network.get_opponent_position()
        if opponent_pos is not None:
            # Host é player1, então o oponente é player2
            if 'player2' in self.players:
                opponent = self.players['player2']
                target_y = opponent_pos
                # Interpolação suave para evitar teleporte
                lerp_paddle = 0.5
                opponent.rect.centery += (target_y - opponent.rect.centery) * lerp_paddle
            # Limpa a posição para não reaplicar
            self.network.clear_opponent_position()


class PauseManager:
    """Gerencia sincronização de pausa entre host e clientes"""
    
    def __init__(self, network, world):
        self.network = network
        self.world = world
        self.paused = False
        self.pause_initiator = None  # "local" ou "remote"
    
    def toggle_pause_local(self):
        """Alterna pausa localmente e notifica rede"""
        new_pause_state = not self.paused
        self.paused = new_pause_state
        self.pause_initiator = "local" if new_pause_state else None
        
        # Notificar rede
        if self.network and new_pause_state:
            self.network.send_pause_request(new_pause_state)
    
    def set_pause(self, paused: bool, initiator: str = "local"):
        """Define estado de pausa e notifica rede se necessário"""
        # Se o estado não mudou, não faz nada
        if self.paused == paused and self.pause_initiator == initiator:
            return
        
        self.paused = paused
        self.pause_initiator = initiator if paused else None
        
        # Se estamos despausando: só cria pause_countdown se estávamos jogando;
        # se estávamos em countdown de gol, apenas retoma o countdown existente.
        if not paused and self.world:
            from settings import FPS
            if self.world.phase == "play":
                self.world.start_pause_countdown(3.0, FPS)
            elif self.world.phase == "countdown":
                self.world.start_countdown(3.0, FPS)
        
        # Notificar rede se for ação local
        if initiator == "local" and self.network:
            self.network.send_pause_request(paused)
    
    def sync_pause_from_network(self):
        """Sincroniza pausa com a rede"""
        if not self.network:
            return
        
        # Verificar se recebemos estado de pausa da rede
        remote_pause_state, initiator = self.network.get_pause_state()
        
        if remote_pause_state is not None:
            # Apenas sincronizar se for pausa remota E não formos nós que pausamos
            if self.pause_initiator != "local":
                if remote_pause_state:
                    # Recebeu pausa do oponente
                    self.set_pause(True, initiator="remote")
                else:
                    # Recebeu despausa do oponente - iniciar countdown
                    self.set_pause(False, initiator="remote")
    
    def reset(self):
        """Reseta o estado de pausa"""
        self.paused = False
        self.pause_initiator = None

