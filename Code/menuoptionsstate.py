from settings import *
from gamestate import BaseState, StateID
import pygame
import os
import math

class OptionsState(BaseState):
    def __init__(self, state_manager):
        super().__init__(state_manager)

       
        font_path = "8-BIT WONDER.TTF"
        if os.path.exists(font_path):
            self.title_font = pygame.font.Font(font_path, 64)
            self.option_font = pygame.font.Font(font_path, 28)
            self.small_font = pygame.font.Font(font_path, 18)
        else:
            self.title_font = pygame.font.Font(None, 64)
            self.option_font = pygame.font.Font(None, 28)
            self.small_font = pygame.font.Font(None, 18)

        # layout
        self.center_x = WINDOW_WIDTH // 2
        self.center_y = WINDOW_HEIGHT // 2
        self.spacing = 50

        # cores 
        
        self.bg_top = (5, 5, 15)
        self.bg_bottom = (10, 10, 40)
        self.panel_color = (15, 15, 35)
        self.panel_border = (80, 80, 150)
        self.text_color = (230, 230, 240)
        self.highlight_color = (255, 220, 120)

        
        self.bg_color = (0, 0, 0)                
        self.center_line_color = (220, 220, 220)  

        # paddles laterais com as mesmas cores dos times
        self.paddle_left_color = OBJECTS_COLORS.get("TEAM_1", (230, 230, 230))
        self.paddle_right_color = OBJECTS_COLORS.get("TEAM_2", (230, 230, 230))

        # painel 
        self.panel_color = (10, 10, 10)
        self.panel_border = (200, 200, 200)
        self.highlight_color = (55, 255, 139)  

        self.time = 0

        # definição das opções
        self.items = [
            {
                "label": "Ball speed",
                "key": "ball_speed",
                "choices": ["Slow", "Normal", "Fast"],
                "values": [300, 400, 550],
                "index": 1,  # começa em Normal
            },
            {
                "label": "Player speed",
                "key": "player_speed",
                "choices": ["Slow", "Normal", "Fast"],
                "values": [350, 500, 650],
                "index": 1,
            },
            {
                "label": "Countdown",
                "key": "countdown",
                "choices": ["Off", "3 sec", "5 sec"],
                "values": [0.0, 3.0, 5.0],
                "index": 1,
            },
            {
                "label": "Back",
                "key": "back",
            },
        ]

        self.current_index = 0

    def _sync_from_settings(self):
        # sincroniza os índices com os valores atuais do jogo
        ball = OBJECTS_SPEED['ball']
        player = OBJECTS_SPEED['player']
        cd = COUNTDOWN['ball']

        def closest_index(values, target):
            return min(range(len(values)), key=lambda i: abs(values[i] - target))

        # ball speed
        self.items[0]["index"] = closest_index(self.items[0]["values"], ball)
        # player speed
        self.items[1]["index"] = closest_index(self.items[1]["values"], player)
        # countdown (trata caso esteja fora da lista)
        if cd in self.items[2]["values"]:
            self.items[2]["index"] = self.items[2]["values"].index(cd)
        else:
            self.items[2]["index"] = 1  # default 3 sec

    def _apply_setting(self, item):
        # aplica o valor selecionado nas configs globais
        if item["key"] == "ball_speed":
            OBJECTS_SPEED['ball'] = item["values"][item["index"]]
        elif item["key"] == "player_speed":
            OBJECTS_SPEED['player'] = item["values"][item["index"]]
        elif item["key"] == "countdown":
            COUNTDOWN['ball'] = item["values"][item["index"]]

    def enter(self, **kwargs):
        self.current_index = 0
        self.time = 0
        self._sync_from_settings()

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.current_index = (self.current_index - 1) % len(self.items)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.current_index = (self.current_index + 1) % len(self.items)
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self._change_value(-1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self._change_value(1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._activate_current()
                elif event.key == pygame.K_ESCAPE:
                    self.state_manager.change_state(StateID.MAIN_MENU)

    def _change_value(self, direction):
        item = self.items[self.current_index]
        if "values" not in item:
            return  # "Back" não tem valor
        max_index = len(item["values"]) - 1
        item["index"] = (item["index"] + direction) % (max_index + 1)
        self._apply_setting(item)

    def _activate_current(self):
        item = self.items[self.current_index]
        if item["key"] == "back":
            self.state_manager.change_state(StateID.MAIN_MENU)

    def update(self, dt):
        self.time += dt

    def _draw_vertical_gradient(self):
        # função original mantida 
        for y in range(WINDOW_HEIGHT):
            t = y / WINDOW_HEIGHT
            r = int(self.bg_top[0] * (1 - t) + self.bg_bottom[0] * t)
            g = int(self.bg_top[1] * (1 - t) + self.bg_bottom[1] * t)
            b = int(self.bg_top[2] * (1 - t) + self.bg_bottom[2] * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WINDOW_WIDTH, y))

    # fundo no estilo Pong: preto, linha central e paddles laterais
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

        # paddles laterais com cores dos times
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

        # leve “scanline” sutil (efeito CRT)
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        for y in range(0, WINDOW_HEIGHT, 4):
            pygame.draw.line(overlay, (255, 255, 255, 15), (0, y), (WINDOW_WIDTH, y))
        self.screen.blit(overlay, (0, 0))

    def draw(self):
       
        self._draw_pong_background()

        panel_width = 560
        panel_height = 380
        panel_rect = pygame.Rect(
            self.center_x - panel_width // 2,
            self.center_y - panel_height // 2,
            panel_width,
            panel_height,
        )
        pygame.draw.rect(self.screen, self.panel_color, panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, self.panel_border, panel_rect, width=2, border_radius=16)

        # título
        title_text = "OPTIONS"
        shadow_surf = self.title_font.render(title_text, True, (0, 0, 0))
        title_surf = self.title_font.render(title_text, True, self.text_color)

        title_rect = title_surf.get_rect(center=(self.center_x, panel_rect.top + 60))
        shadow_rect = shadow_surf.get_rect(center=(self.center_x + 3, panel_rect.top + 63))

        self.screen.blit(shadow_surf, shadow_rect)
        self.screen.blit(title_surf, title_rect)

        # barra sob o título (estilo pong)
        bar_width = 160
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

        for i, item in enumerate(self.items):
            y = start_y + i * self.spacing

            is_selected = (i == self.current_index)
            color = self.highlight_color if is_selected else self.text_color

            # label da opção
            label_surf = self.option_font.render(item["label"], True, color)
            label_rect = label_surf.get_rect(midleft=(self.center_x - 180, y))
            self.screen.blit(label_surf, label_rect)

            # valor (se tiver)
            if "choices" in item:
                choice = item["choices"][item["index"]]
                value_surf = self.option_font.render(choice, True, color)
                value_rect = value_surf.get_rect(midright=(self.center_x + 180, y))
                self.screen.blit(value_surf, value_rect)

            # cursor
            if is_selected:
                offset = 6 * math.sin(self.time * 6)
                cursor_height = label_rect.height - 6
                cursor_rect = pygame.Rect(
                    label_rect.left - 26 + offset,
                    label_rect.centery - cursor_height // 2,
                    10,
                    cursor_height
                )
                pygame.draw.rect(self.screen, self.highlight_color, cursor_rect, border_radius=3)
        '''
        # footer
        footer_text = "↑↓: navigate  •  ←→: change  •  ENTER/ESC: back"
        footer_surf = self.small_font.render(footer_text, True, (180, 180, 200))
        footer_rect = footer_surf.get_rect(center=(self.center_x, panel_rect.bottom - 25))
        self.screen.blit(footer_surf, footer_rect)
        '''
    def exit(self):
        pass
