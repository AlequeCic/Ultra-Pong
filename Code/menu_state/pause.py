from settings import *

class PauseMenu:
    def __init__(self, screen, title_font, option_font, small_font):
        self.screen = screen
        self.title_font = title_font
        self.option_font = option_font
        self.small_font = small_font
        
        self.pause_options = ["Resume", "Main Menu", "Quit"]
        self.index = 0
        
        # Configurações de cores
        self.panel_color = (10, 10, 10)
        self.panel_border = (200, 200, 200)
        self.text_color = (230, 230, 240)
        self.highlight_color = (55, 255, 139)
        
        # Animação de dots
        self.pause_dots = ""
        self.dot_timer = 0.0
        self.dot_interval = 0.5
    
    def update_dot_animation(self, dt):
        self.dot_timer += dt
        if self.dot_timer >= self.dot_interval:
            self.dot_timer = 0
            self.pause_dots = "." if len(self.pause_dots) >= 3 else self.pause_dots + "."
    
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.index = (self.index - 1) % len(self.pause_options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.index = (self.index + 1) % len(self.pause_options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return self.pause_options[self.index]
                elif event.key == pygame.K_ESCAPE:
                    return "Resume"
        return None
    
    def draw(self, center_x, center_y, title_text="PAUSED", show_options=True, show_dots=False):
        # Overlay escuro
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Ajusta altura do painel baseado no conteúdo
        panel_height = 280 if show_options else 200
        panel_width = 520
        
        panel_rect = pygame.Rect(
            center_x - panel_width // 2,
            center_y - panel_height // 2,
            panel_width,
            panel_height,
        )
        
        # Painel
        pygame.draw.rect(self.screen, self.panel_color, panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, self.panel_border, panel_rect, width=2, border_radius=16)
        
        # Título
        title_surf = self.title_font.render(title_text, True, self.text_color)
        title_rect = title_surf.get_rect(center=(center_x, panel_rect.top + 60))
        self.screen.blit(title_surf, title_rect)
        
        # Barra decorativa
        if show_options:
            bar_width = 140
            bar_height = 6
            bar_rect = pygame.Rect(
                center_x - bar_width // 2,
                title_rect.bottom + 8,
                bar_width,
                bar_height
            )
            pygame.draw.rect(self.screen, (220, 220, 220), bar_rect)
        
        # Opções do menu (se mostrado)
        if show_options:
            start_y = title_rect.bottom + 35
            spacing = 40
            
            for i, text in enumerate(self.pause_options):
                y = start_y + i * spacing
                selected = (i == self.index)
                color = self.highlight_color if selected else self.text_color
                
                option_surf = self.option_font.render(text, True, color)
                option_rect = option_surf.get_rect(center=(center_x, y))
                self.screen.blit(option_surf, option_rect)
                
                if selected:
                    cursor_height = option_rect.height - 6
                    cursor_rect = pygame.Rect(
                        option_rect.left - 26,
                        option_rect.centery - cursor_height // 2,
                        10,
                        cursor_height
                    )
                    pygame.draw.rect(self.screen, self.highlight_color, cursor_rect, border_radius=3)
        
        # Mensagem com dots (para pause remoto)
        if show_dots:
            instr_text = "Waiting for opponent to resume" + self.pause_dots
            instr_surf = self.small_font.render(instr_text, True, self.text_color)
            instr_rect = instr_surf.get_rect(center=(center_x, panel_rect.bottom - 40))
            self.screen.blit(instr_surf, instr_rect)
    
    def reset(self):
        self.index = 0
        self.pause_dots = ""
        self.dot_timer = 0.0


class RemotePauseMessage:
    def __init__(self, screen, title_font, option_font, small_font):
        self.screen = screen
        self.title_font = title_font
        self.option_font = option_font
        self.small_font = small_font
        
        # Configurações de cores
        self.panel_color = (10, 10, 10)
        self.panel_border = (200, 200, 200)
        self.text_color = (230, 230, 240)
        self.highlight_color = (55, 255, 139)
        
        # Animação de dots
        self.pause_dots = ""
        self.dot_timer = 0.0
        self.dot_interval = 0.5
    
    def update_dot_animation(self, dt):
        self.dot_timer += dt
        if self.dot_timer >= self.dot_interval:
            self.dot_timer = 0
            self.pause_dots = "." if len(self.pause_dots) >= 3 else self.pause_dots + "."
    
    def draw(self, center_x, center_y):
        # Overlay escuro
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        panel_width = 520
        panel_height = 200
        
        panel_rect = pygame.Rect(
            center_x - panel_width // 2,
            center_y - panel_height // 2,
            panel_width,
            panel_height,
        )
        
        # Painel
        pygame.draw.rect(self.screen, self.panel_color, panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, self.panel_border, panel_rect, width=2, border_radius=16)
        
        # Título
        title_text = "GAME PAUSED"
        title_surf = self.title_font.render(title_text, True, self.text_color)
        title_rect = title_surf.get_rect(center=(center_x, panel_rect.top + 60))
        self.screen.blit(title_surf, title_rect)
        
        # Mensagem principal
        msg_text = "Opponent paused the game"
        msg_surf = self.option_font.render(msg_text, True, self.highlight_color)
        msg_rect = msg_surf.get_rect(center=(center_x, center_y))
        self.screen.blit(msg_surf, msg_rect)
        
        # Mensagem de espera com dots
        instr_text = "Waiting for opponent to resume" + self.pause_dots
        instr_surf = self.small_font.render(instr_text, True, self.text_color)
        instr_rect = instr_surf.get_rect(center=(center_x, center_y + 40))
        self.screen.blit(instr_surf, instr_rect)
    
    def reset(self):
        self.pause_dots = ""
        self.dot_timer = 0.0


class DisconnectMessage:
    def __init__(self, screen, title_font, small_font):
        self.screen = screen
        self.title_font = title_font
        self.small_font = small_font
    
    def draw(self, center_x, center_y, disconnect_timer, message_duration=3.0):
        # Overlay
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        # Texto principal
        msg_text = "OPPONENT DISCONNECTED"
        msg_surf = self.title_font.render(msg_text, True, (255, 100, 100))
        msg_rect = msg_surf.get_rect(center=(center_x, center_y - 20))
        self.screen.blit(msg_surf, msg_rect)
        
        # Contador
        remaining = max(0, message_duration - disconnect_timer)
        sub_text = f"Returning to menu in {int(remaining) + 1}..."
        sub_surf = self.small_font.render(sub_text, True, (180, 180, 200))
        sub_rect = sub_surf.get_rect(center=(center_x, center_y + 30))
        self.screen.blit(sub_surf, sub_rect)