from settings import *
from gamestate import BaseState, StateID
from audio_manager import get_audio_manager
import pygame
import os
import math

class MainMenuState(BaseState):
    def __init__(self, state_manager):
        super().__init__(state_manager)

        font_path = "8-BIT WONDER.TTF"
        if os.path.exists(font_path):
            self.title_font = pygame.font.Font(font_path, 72)
            self.option_font = pygame.font.Font(font_path, 32)
            self.small_font = pygame.font.Font(font_path, 18)
        else:
            self.title_font = pygame.font.Font(None, 72)
            self.option_font = pygame.font.Font(None, 32)
            self.small_font = pygame.font.Font(None, 18)

        # opções do menu 
        self.options = ["Start Game", "Multiplayer", "Options", "Quit"]
        self.current_index = 0

        self.center_x = WINDOW_WIDTH // 2
        self.center_y = WINDOW_HEIGHT // 2
        self.spacing = 50

        # cores base 
        self.bg_color = (0, 0, 0)                 # fundo preto clássico
        self.center_line_color = (220, 220, 220)  # linha central

        # paddles decorativos 
        self.paddle_left_color = OBJECTS_COLORS.get("TEAM_1", (230, 230, 230))
        self.paddle_right_color = OBJECTS_COLORS.get("TEAM_2", (230, 230, 230))

        self.panel_color = (10, 10, 10)           
        self.panel_border = (200, 200, 200)      
        self.text_color = (230, 230, 240)         
        self.highlight_color = (55, 255, 139)     
        self.shadow_color = (0, 0, 0)            

        self.time = 0

    def enter(self, **kwargs):
        self.current_index = 0
        self.time = 0
        get_audio_manager().play_main_theme()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.current_index = (self.current_index - 1) % len(self.options)
                    get_audio_manager().play_menu_hover()
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.current_index = (self.current_index + 1) % len(self.options)
                    get_audio_manager().play_menu_hover()
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    get_audio_manager().play_menu_click()
                    self._activate_option()
                elif event.key == pygame.K_ESCAPE:
                    self.state_manager.quit()

    def _activate_option(self):
        option = self.options[self.current_index]

        if option == "Start Game":
            self.state_manager.change_state(StateID.PLAYING)

        elif option == "Multiplayer":
            # vai para a Tela 1 (escolher 1v1 / 2v2)
            self.state_manager.change_state(StateID.MULTI_MODE)

        elif option == "Options":
            self.state_manager.change_state(StateID.OPTIONS)

        elif option == "Quit":
            self.state_manager.quit()

    def update(self, dt):
        self.time += dt

    # fundo 
    def _draw_pong_background(self):
        # fundo
        self.screen.fill(self.bg_color)

        # linha central pontilhada
        dash_height = 18
        gap = 10
        x = WINDOW_WIDTH // 2
        for y in range(0, WINDOW_HEIGHT, dash_height + gap):
            pygame.draw.rect(
                self.screen,
                self.center_line_color,
                (x - 2, y, 4, dash_height)
            )

        # paddles decorativos 
        paddle_width = 8
        paddle_height = 70
        offset_y = 40  

        left_rect = pygame.Rect(
            40,
            self.center_y - paddle_height // 2 - offset_y,
            paddle_width,
            paddle_height
        )
        right_rect = pygame.Rect(
            WINDOW_WIDTH - 40 - paddle_width,
            self.center_y - paddle_height // 2 + offset_y,
            paddle_width,
            paddle_height
        )
        pygame.draw.rect(self.screen, self.paddle_left_color, left_rect)
        pygame.draw.rect(self.screen, self.paddle_right_color, right_rect)

        
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        for y in range(0, WINDOW_HEIGHT, 4):
            pygame.draw.line(overlay, (255, 255, 255, 15), (0, y), (WINDOW_WIDTH, y))
        self.screen.blit(overlay, (0, 0))

    def draw(self):
        # fundo 
        self._draw_pong_background()

        # painel central 
        panel_width = 520
        panel_height = 340
        panel_rect = pygame.Rect(
            self.center_x - panel_width // 2,
            self.center_y - panel_height // 2,
            panel_width,
            panel_height,
        )

        
        pygame.draw.rect(self.screen, self.panel_color, panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, self.panel_border, panel_rect, width=2, border_radius=16)

        # título com “glow”
        title_text = "ULTRA PONG"

        # sombra leve
        shadow_surf = self.title_font.render(title_text, True, self.shadow_color)
        shadow_rect = shadow_surf.get_rect(center=(self.center_x + 3, panel_rect.top + 68))

        
        glow_surf = self.title_font.render(title_text, True, self.highlight_color)
        glow_rect = glow_surf.get_rect(center=(self.center_x, panel_rect.top + 68))

        
        title_surf = self.title_font.render(title_text, True, self.text_color)
        title_rect = title_surf.get_rect(center=(self.center_x, panel_rect.top + 68))

        self.screen.blit(shadow_surf, shadow_rect)
        self.screen.blit(glow_surf, glow_rect)
        self.screen.blit(title_surf, title_rect)

        # pequena barra “pong” embaixo do título
        bar_width = 140
        bar_height = 6
        bar_rect = pygame.Rect(
            self.center_x - bar_width // 2,
            title_rect.bottom + 8,
            bar_width,
            bar_height
        )
        pygame.draw.rect(self.screen, self.center_line_color, bar_rect)

        # opções
        start_y = title_rect.bottom + 40

        for i, text in enumerate(self.options):
            y = start_y + i * self.spacing

            is_selected = (i == self.current_index)
            color = self.highlight_color if is_selected else self.text_color

            
            option_surf = self.option_font.render(text, True, color)
            option_rect = option_surf.get_rect(center=(self.center_x, y))
            self.screen.blit(option_surf, option_rect)

            if is_selected:
                # cursor 
                offset = 6 * math.sin(self.time * 6)
                cursor_height = option_rect.height - 8
                cursor_rect = pygame.Rect(
                    option_rect.left - 24 + offset, 
                    option_rect.centery - cursor_height // 2,
                    10,
                    cursor_height
                )
                pygame.draw.rect(self.screen, self.highlight_color, cursor_rect, border_radius=3)
    '''
        subtítulo embaixo, deixei como comentario aqui, pq achei que poluia visualmente, mas se vcs acharem melhor ter, so apagar as #s
        footer_text = "ENTER: select  •  ESC: quit"
        footer_surf = self.small_font.render(footer_text, True, (180, 180, 200))
        footer_rect = footer_surf.get_rect(center=(self.center_x, panel_rect.bottom - 25))
        self.screen.blit(footer_surf, footer_rect)
    '''
    def exit(self):
        pass
