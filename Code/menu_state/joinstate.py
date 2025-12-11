import os
from gamestate import BaseState, StateID
from network.network_handler import NetworkHandler
from audio_manager import get_audio_manager
from settings import *

class JoinState(BaseState):
    def __init__(self, state_manager):
        super().__init__(state_manager)
        
        # input
        self.ip_text = "localhost"
        self.port_text = "5555"
        self.active_field = "ip"  # "ip" or "port"
        self.error_message = ""
        
        # Fonts
        font_path = "8-BIT WONDER.TTF"
        if os.path.exists(font_path):
            self.title_font = pygame.font.Font(font_path, 48)
            self.label_font = pygame.font.Font(font_path, 28)
            self.input_font = pygame.font.Font(font_path, 24)
            self.small_font = pygame.font.Font(font_path, 18)
        else:
            self.title_font = pygame.font.Font(None, 48)
            self.label_font = pygame.font.Font(None, 28)
            self.input_font = pygame.font.Font(None, 24)
            self.small_font = pygame.font.Font(None, 18)
        
        # Colors
        self.bg_color = (0, 0, 0)
        self.text_color = (230, 230, 240)
        self.highlight_color = (55, 255, 139)
        self.error_color = (255, 100, 100)
        
        # Cursor
        self.cursor_visible = True
        self.cursor_timer = 0

    def enter(self, **kwargs):
        self.ip_text = "localhost"
        self.port_text = "5555"
        self.active_field = "ip"
        self.error_message = ""
        self.cursor_visible = True
        self.cursor_timer = 0

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state_manager.change_state(StateID.MULTI_HOST_JOIN)
                
                elif event.key == pygame.K_TAB:
                    # Changing camps
                    get_audio_manager().play_menu_hover()
                    self.active_field = "port" if self.active_field == "ip" else "ip"
                
                elif event.key == pygame.K_RETURN:
                    get_audio_manager().play_menu_click()
                    self._try_connect()
                
                elif event.key == pygame.K_BACKSPACE:
                    # Erasing chars
                    if self.active_field == "ip":
                        self.ip_text = self.ip_text[:-1]
                    else:
                        self.port_text = self.port_text[:-1]
                
                else:
                    # Adding chars
                    char = event.unicode
                    if char.isprintable():
                        if self.active_field == "ip":
                            if char.isdigit() or char == '.':
                                self.ip_text += char
                        else:
                            if char.isdigit():
                                self.port_text += char

    def _try_connect(self):
        try:
            port = int(self.port_text)
            network = NetworkHandler()
            
            if network.join(self.ip_text, port):
                self.state_manager.change_state(StateID.WAITING, 
                                              network=network, 
                                              mode="1v1",
                                              is_host=False)
            else:
                self.error_message = "Connection failed"
                
        except ValueError:
            self.error_message = "Invalid port number"

    def update(self, dt):
        # Cursor 
        self.cursor_timer += dt
        if self.cursor_timer > 0.5:
            self.cursor_timer = 0
            self.cursor_visible = not self.cursor_visible

    def draw(self):
        # Bg
        self.screen.fill(self.bg_color)
        
        # Central line
        dash_height = 18
        gap = 10
        x = WINDOW_WIDTH // 2
        for y in range(0, WINDOW_HEIGHT, dash_height + gap):
            pygame.draw.rect(
                self.screen,
                (220, 220, 220),
                (x - 2, y, 4, dash_height)
            )
        
        # Central panel
        panel_width = 500
        panel_height = 350
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
        
        # Title
        title_text = "JOIN GAME"
        title_surf = self.title_font.render(title_text, True, self.highlight_color)
        title_rect = title_surf.get_rect(center=(center_x, panel_rect.top + 60))
        self.screen.blit(title_surf, title_rect)
        
        y_offset = 120
        
        # IP
        ip_label = self.label_font.render("IP Address:", True, self.text_color)
        ip_label_rect = ip_label.get_rect(midright=(center_x - 10, panel_rect.top + y_offset))
        self.screen.blit(ip_label, ip_label_rect)
        
        ip_color = self.highlight_color if self.active_field == "ip" else self.text_color
        ip_display = self.ip_text
        if self.active_field == "ip" and self.cursor_visible:
            ip_display += "_"
        
        ip_surf = self.input_font.render(ip_display, True, ip_color)
        ip_rect = ip_surf.get_rect(midleft=(center_x + 10, panel_rect.top + y_offset))
        self.screen.blit(ip_surf, ip_rect)
        
        #Port
        port_label = self.label_font.render("Port:", True, self.text_color)
        port_label_rect = port_label.get_rect(midright=(center_x - 10, panel_rect.top + y_offset + 50))
        self.screen.blit(port_label, port_label_rect)
        
        port_color = self.highlight_color if self.active_field == "port" else self.text_color
        port_display = self.port_text
        if self.active_field == "port" and self.cursor_visible:
            port_display += "_"
        
        port_surf = self.input_font.render(port_display, True, port_color)
        port_rect = port_surf.get_rect(midleft=(center_x + 10, panel_rect.top + y_offset + 50))
        self.screen.blit(port_surf, port_rect)
        
        # Error message
        if self.error_message:
            error_surf = self.small_font.render(self.error_message, True, self.error_color)
            error_rect = error_surf.get_rect(center=(center_x, panel_rect.top + y_offset + 100))
            self.screen.blit(error_surf, error_rect)
        
        # Instructions
        instr1 = "TAB: Switch field | ENTER: Connect | ESC: Back"
        instr1_surf = self.small_font.render(instr1, True, (180, 180, 200))
        instr1_rect = instr1_surf.get_rect(center=(center_x, panel_rect.bottom - 30))
        self.screen.blit(instr1_surf, instr1_rect)