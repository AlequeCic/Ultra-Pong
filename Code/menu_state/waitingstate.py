import os
import socket
from gamestate import BaseState, StateID
from settings import *

class WaitingForPlayersState(BaseState):
    def __init__(self, state_manager):
        super().__init__(state_manager)
        
        # Configuração da rede
        self.network = None
        self.mode = "1v1"
        self.message = "Waiting for opponent..."
        self.is_host = False
        
        # Fontes
        font_path = "8-BIT WONDER.TTF"
        if os.path.exists(font_path):
            self.title_font = pygame.font.Font(font_path, 56)
            self.text_font = pygame.font.Font(font_path, 24)
            self.small_font = pygame.font.Font(font_path, 18)
        else:
            self.title_font = pygame.font.Font(None, 56)
            self.text_font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 18)
        
        # colors
        self.bg_color = (0, 0, 0)
        self.text_color = (230, 230, 240)
        self.highlight_color = (55, 255, 139)
        
        # dot animation
        self.dot_timer = 0
        self.dots = ""
        
        # time counter
        self.wait_time = 0

    def enter(self, network=None, mode="1v1", is_host=False):
        self.network = network
        self.mode = mode
        self.is_host = is_host
        self.dot_timer = 0
        self.dots = ""
        self.wait_time = 0
        self.local_ip = self._get_local_ip() if is_host else ""
        
        if self.is_host:
            self.message = f"Hosting {mode} match..."
        else:
            self.message = "Connecting to host..."
    
    def _get_local_ip(self):
        """Obtém o IP local da máquina"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # disconnect
                    if self.network:
                        self.network.disconnect()
                    self.state_manager.change_state(StateID.MULTI_HOST_JOIN)

    def update(self, dt):
        self.wait_time += dt
        self.dot_timer += dt
        
        # dot animation
        if self.dot_timer > 0.5:
            self.dot_timer = 0
            self.dots = "." if len(self.dots) >= 3 else self.dots + "."
        
        # network update
        if self.network:
            self.network.update()
            
            # verifying if net is ready
            if self.network.is_ready():
                self.state_manager.change_state(StateID.PLAYING, 
                                              game_mode="multiplayer_1v1", 
                                              network=self.network)

    def draw(self):
        # bg
        self.screen.fill(self.bg_color)
        
        # center dot line
        dash_height = 18
        gap = 10
        x = WINDOW_WIDTH // 2
        for y in range(0, WINDOW_HEIGHT, dash_height + gap):
            pygame.draw.rect(
                self.screen,
                (220, 220, 220),
                (x - 2, y, 4, dash_height)
            )
        
        # main painel
        panel_width = 500
        panel_height = 300
        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2
        
        panel_rect = pygame.Rect(
            center_x - panel_width // 2,
            center_y - panel_height // 2,
            panel_width,
            panel_height,
        )
        
        pygame.draw.rect(self.screen, (20, 20, 20), panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, (100, 100, 100), panel_rect, width=2, border_radius=16)
        
        # title
        title_text = "WAITING"
        title_surf = self.title_font.render(title_text, True, self.highlight_color)
        title_rect = title_surf.get_rect(center=(center_x, panel_rect.top + 60))
        self.screen.blit(title_surf, title_rect)
        
        # message
        msg_surf = self.text_font.render(self.message + self.dots, True, self.text_color)
        msg_rect = msg_surf.get_rect(center=(center_x, center_y - 30))
        self.screen.blit(msg_surf, msg_rect)
        
        # aditional information
        if self.is_host:
            # Mostrar IP em destaque
            ip_text = f"IP: {self.local_ip}"
            ip_surf = self.text_font.render(ip_text, True, self.highlight_color)
            ip_rect = ip_surf.get_rect(center=(center_x, center_y + 10))
            self.screen.blit(ip_surf, ip_rect)
            
            # Mostrar porta
            port_text = f"Port: 5555"
            port_surf = self.small_font.render(port_text, True, (180, 180, 200))
            port_rect = port_surf.get_rect(center=(center_x, center_y + 45))
            self.screen.blit(port_surf, port_rect)
        
        # waiting time
        time_text = f"Waiting: {int(self.wait_time)}s"
        time_surf = self.small_font.render(time_text, True, (150, 150, 150))
        time_rect = time_surf.get_rect(center=(center_x, panel_rect.bottom - 40))
        self.screen.blit(time_surf, time_rect)
        
        # instructions
        instr_text = "Press ESC to cancel"
        instr_surf = self.small_font.render(instr_text, True, (200, 100, 100))
        instr_rect = instr_surf.get_rect(center=(center_x, panel_rect.bottom - 20))
        self.screen.blit(instr_surf, instr_rect)