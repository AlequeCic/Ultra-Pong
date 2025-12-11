from settings import *
from gamestate import BaseState, StateID
from audio_manager import get_audio_manager
import os
import math
from network.network_handler import NetworkHandler

# TELA 1: escolher modo (1v1 / 2v2)
class MultiplayerModeState(BaseState):
    def __init__(self, state_manager):
        super().__init__(state_manager)

        font_path = "8-BIT WONDER.TTF"
        if os.path.exists(font_path):
            self.title_font = pygame.font.Font(font_path, 64)
            self.option_font = pygame.font.Font(font_path, 30)
            self.small_font = pygame.font.Font(font_path, 18)
        else:
            self.title_font = pygame.font.Font(None, 64)
            self.option_font = pygame.font.Font(None, 30)
            self.small_font = pygame.font.Font(None, 18)

        self.options = ["1 vs 1", "2 vs 2", "Back"]
        self.current_index = 0

        self.center_x = WINDOW_WIDTH // 2
        self.center_y = WINDOW_HEIGHT // 2
        self.spacing = 50

        # Cores
        self.bg_color = (0, 0, 0)
        self.center_line_color = (220, 220, 220)
        self.paddle_left_color = OBJECTS_COLORS.get("TEAM_1", (230, 230, 230))
        self.paddle_right_color = OBJECTS_COLORS.get("TEAM_2", (230, 230, 230))
        self.panel_color = (10, 10, 10)
        self.panel_border = (200, 200, 200)
        self.text_color = (230, 230, 240)
        self.highlight_color = (55, 255, 139)
        self.disabled_color = (100, 100, 100)  #cor para itens desabilitados (2v2)

        self.time = 0
        self.selected_mode = None  # "1v1" ou "2v2"

    def enter(self, **kwargs):
        self.current_index = 0
        self.time = 0
        self.selected_mode = None

        #para o 2v2
        self.message = ""
        self.message_timer = 0

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
                    self.state_manager.change_state(StateID.MAIN_MENU)

    def _activate_option(self):
        option = self.options[self.current_index]

        if option == "1 vs 1":
            self.selected_mode = "1v1"
            # vai para escolher hospedar/entrar
            self.state_manager.change_state(StateID.MULTI_HOST_JOIN, mode=self.selected_mode)

        elif option == "2 vs 2":
            # Mostrar mensagem de que está em desenvolvimento
            self.message = "2v2 mode coming soon!"
            self.message_timer = 2.0  # Mostrar por 2 segundos

        elif option == "Back":
            self.state_manager.change_state(StateID.MAIN_MENU)

    def update(self, dt):
        self.time += dt

        #atualizando a mensagem
        # Atualizar timer da mensagem
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ""

    def _draw_vertical_gradient(self):
        for y in range(WINDOW_HEIGHT):
            t = y / WINDOW_HEIGHT
            r = int(self.bg_top[0] * (1 - t) + self.bg_bottom[0] * t)
            g = int(self.bg_top[1] * (1 - t) + self.bg_bottom[1] * t)
            b = int(self.bg_top[2] * (1 - t) + self.bg_bottom[2] * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WINDOW_WIDTH, y))

    # fundo 
    def _draw_pong_background(self):
        self.screen.fill(self.bg_color)

        # linha central pontilhada
        dash_h = 18
        gap = 10
        x = WINDOW_WIDTH // 2
        for y in range(0, WINDOW_HEIGHT, dash_h + gap):
            pygame.draw.rect(
                self.screen,
                self.center_line_color,
                (x - 2, y, 4, dash_h)
            )

        # paddles laterais 
        paddle_w = 8
        paddle_h = 70
        offset_y = 40

        left_rect = pygame.Rect(
            40,
            self.center_y - paddle_h // 2 - offset_y,
            paddle_w,
            paddle_h
        )
        right_rect = pygame.Rect(
            WINDOW_WIDTH - 40 - paddle_w,
            self.center_y - paddle_h // 2 + offset_y,
            paddle_w,
            paddle_h
        )
        pygame.draw.rect(self.screen, self.paddle_left_color, left_rect)
        pygame.draw.rect(self.screen, self.paddle_right_color, right_rect)

        # scanlines
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        for y in range(0, WINDOW_HEIGHT, 4):
            pygame.draw.line(overlay, (255, 255, 255, 15), (0, y), (WINDOW_WIDTH, y))
        self.screen.blit(overlay, (0, 0))

    def draw(self):
        # fundo 
        self._draw_pong_background()

        panel_width = 540
        panel_height = 320
        panel_rect = pygame.Rect(
            self.center_x - panel_width // 2,
            self.center_y - panel_height // 2,
            panel_width,
            panel_height,
        )
        pygame.draw.rect(self.screen, self.panel_color, panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, self.panel_border, panel_rect, width=2, border_radius=16)

        title_text = "MULTIPLAYER"
        shadow_surf = self.title_font.render(title_text, True, (0, 0, 0))
        title_surf = self.title_font.render(title_text, True, self.text_color)

        title_rect = title_surf.get_rect(center=(self.center_x, panel_rect.top + 60))
        shadow_rect = shadow_surf.get_rect(center=(self.center_x + 3, panel_rect.top + 63))

        self.screen.blit(shadow_surf, shadow_rect)
        self.screen.blit(title_surf, title_rect)

        # barra sob o título
        bar_width = 160
        bar_height = 6
        bar_rect = pygame.Rect(
            self.center_x - bar_width // 2,
            title_rect.bottom + 8,
            bar_width,
            bar_height
        )
        pygame.draw.rect(self.screen, self.center_line_color, bar_rect)

        subtitle = "Select mode"
        subtitle_surf = self.small_font.render(subtitle, True, (190, 190, 210))
        subtitle_rect = subtitle_surf.get_rect(center=(self.center_x, title_rect.bottom + 30))
        self.screen.blit(subtitle_surf, subtitle_rect)

        start_y = subtitle_rect.bottom + 25

        for i, text in enumerate(self.options):
            y = start_y + i * self.spacing
            is_selected = (i == self.current_index)
            color = self.highlight_color if is_selected else self.text_color

            # Verificar se é a opção 2v2 (índice 1)
            if i == 1:  # 2 vs 2 está desabilitado
                color = self.disabled_color
            else:
                color = self.highlight_color if is_selected else self.text_color

            option_surf = self.option_font.render(text, True, color)
            option_rect = option_surf.get_rect(center=(self.center_x, y))
            self.screen.blit(option_surf, option_rect)

            if is_selected:
                # cursor animated
                offset = 6 * math.sin(self.time * 6)
                cursor_height = option_rect.height - 8
                cursor_rect = pygame.Rect(
                    option_rect.left - 24 + offset,
                    option_rect.centery - cursor_height // 2,
                    10,
                    cursor_height
                )
                pygame.draw.rect(self.screen, self.highlight_color, cursor_rect, border_radius=3)

        # Mensagem temporária
        if self.message:
            msg_surf = self.small_font.render(self.message, True, (255, 200, 100))
            msg_rect = msg_surf.get_rect(center=(self.center_x, panel_rect.bottom - 50))
            self.screen.blit(msg_surf, msg_rect)

        footer_text = "ENTER: selecionar  •  ESC: voltar"
        footer_surf = self.small_font.render(footer_text, True, (180, 180, 200))
        footer_rect = footer_surf.get_rect(center=(self.center_x, panel_rect.bottom - 25))
        self.screen.blit(footer_surf, footer_rect)

# Basicamente a mesma coisa da tela anterior, mas agora escolhe se vai hospedar ou entrar, entao é meio que o mesmo que ai em cima, nao sei se tinha como otimizar pra deixar o codigo menor, entao fiz manualmente...
# TELA 2: escolher se vai hospedar ou entrar
class MultiplayerHostJoinState(BaseState):
    def __init__(self, state_manager):
        super().__init__(state_manager)

        font_path = "8-BIT WONDER.TTF"
        if os.path.exists(font_path):
            self.title_font = pygame.font.Font(font_path, 56)
            self.option_font = pygame.font.Font(font_path, 30)
            self.small_font = pygame.font.Font(font_path, 18)
        else:
            self.title_font = pygame.font.Font(None, 56)
            self.option_font = pygame.font.Font(None, 30)
            self.small_font = pygame.font.Font(None, 18)

        self.options = ["Host match", "Join match", "Back"]
        self.current_index = 0

        self.center_x = WINDOW_WIDTH // 2
        self.center_y = WINDOW_HEIGHT // 2
        self.spacing = 50

        

        # Cores
        self.bg_color = (0, 0, 0)
        self.center_line_color = (220, 220, 220)
        self.paddle_left_color = OBJECTS_COLORS.get("TEAM_1", (230, 230, 230))
        self.paddle_right_color = OBJECTS_COLORS.get("TEAM_2", (230, 230, 230))
        self.panel_color = (10, 10, 10)
        self.panel_border = (200, 200, 200)
        self.text_color = (230, 230, 240)
        self.highlight_color = (55, 255, 139)

        self.time = 0
        self.mode = "?"  # "1v1" ou "2v2"

    def enter(self, mode="1v1", **kwargs):
        self.current_index = 0
        self.time = 0
        self.mode = mode  # informação vinda da tela anterior

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
                    # volta pra escolha de modo
                    self.state_manager.change_state(StateID.MULTI_MODE)

    def _activate_option(self):
        option = self.options[self.current_index]

        if option == "Host match":
            # Criar servidor e ir para tela de espera
            network = NetworkHandler()
            if network.host(5555):  # Porta padrão
                self.state_manager.change_state(StateID.WAITING, 
                                              network=network, 
                                              mode=self.mode,
                                              is_host=True)
            else:
                print("Failed to host server")

        elif option == "Join match":
            # Ir para tela de inserir IP
            self.state_manager.change_state(StateID.JOIN)

        elif option == "Back":
            self.state_manager.change_state(StateID.MULTI_MODE)


    def update(self, dt):
        self.time += dt

    def _draw_vertical_gradient(self):
        for y in range(WINDOW_HEIGHT):
            t = y / WINDOW_HEIGHT
            r = int(self.bg_top[0] * (1 - t) + self.bg_bottom[0] * t)
            g = int(self.bg_top[1] * (1 - t) + self.bg_bottom[1] * t)
            b = int(self.bg_top[2] * (1 - t) + self.bg_bottom[2] * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WINDOW_WIDTH, y))

    def _draw_pong_background(self):
        self.screen.fill(self.bg_color)

        # linha central pontilhada
        dash_h = 18
        gap = 10
        x = WINDOW_WIDTH // 2
        for y in range(0, WINDOW_HEIGHT, dash_h + gap):
            pygame.draw.rect(
                self.screen,
                self.center_line_color,
                (x - 2, y, 4, dash_h)
            )

        # paddles laterais
        paddle_w = 8
        paddle_h = 70
        offset_y = 40

        left_rect = pygame.Rect(
            40,
            self.center_y - paddle_h // 2 - offset_y,
            paddle_w,
            paddle_h
        )
        right_rect = pygame.Rect(
            WINDOW_WIDTH - 40 - paddle_w,
            self.center_y - paddle_h // 2 + offset_y,
            paddle_w,
            paddle_h
        )
        pygame.draw.rect(self.screen, self.paddle_left_color, left_rect)
        pygame.draw.rect(self.screen, self.paddle_right_color, right_rect)

        # scanlines
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        for y in range(0, WINDOW_HEIGHT, 4):
            pygame.draw.line(overlay, (255, 255, 255, 15), (0, y), (WINDOW_WIDTH, y))
        self.screen.blit(overlay, (0, 0))

    def draw(self):
        # fundo 
        self._draw_pong_background()

        panel_width = 540
        panel_height = 320
        panel_rect = pygame.Rect(
            self.center_x - panel_width // 2,
            self.center_y - panel_height // 2,
            panel_width,
            panel_height,
        )
        pygame.draw.rect(self.screen, self.panel_color, panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, self.panel_border, panel_rect, width=2, border_radius=16)

        title_text = f"{self.mode.upper()} - MULTI"
        shadow_surf = self.title_font.render(title_text, True, (0, 0, 0))
        title_surf = self.title_font.render(title_text, True, self.text_color)

        title_rect = title_surf.get_rect(center=(self.center_x, panel_rect.top + 60))
        shadow_rect = shadow_surf.get_rect(center=(self.center_x + 3, panel_rect.top + 63))

        self.screen.blit(shadow_surf, shadow_rect)
        self.screen.blit(title_surf, title_rect)

        # barra sob o título
        bar_width = 200
        bar_height = 6
        bar_rect = pygame.Rect(
            self.center_x - bar_width // 2,
            title_rect.bottom + 8,
            bar_width,
            bar_height
        )
        pygame.draw.rect(self.screen, self.center_line_color, bar_rect)

        subtitle = "Select connection type"
        subtitle_surf = self.small_font.render(subtitle, True, (190, 190, 210))
        subtitle_rect = subtitle_surf.get_rect(center=(self.center_x, title_rect.bottom + 30))
        self.screen.blit(subtitle_surf, subtitle_rect)

        start_y = subtitle_rect.bottom + 25

        for i, text in enumerate(self.options):
            y = start_y + i * self.spacing
            is_selected = (i == self.current_index)
            color = self.highlight_color if is_selected else self.text_color

            option_surf = self.option_font.render(text, True, color)
            option_rect = option_surf.get_rect(center=(self.center_x, y))
            self.screen.blit(option_surf, option_rect)

            if is_selected:
                # cursor animated
                offset = 6 * math.sin(self.time * 6)
                cursor_height = option_rect.height - 8
                cursor_rect = pygame.Rect(
                    option_rect.left - 24 + offset,
                    option_rect.centery - cursor_height // 2,
                    10,
                    cursor_height
                )
                pygame.draw.rect(self.screen, self.highlight_color, cursor_rect, border_radius=3)

        footer_text = "ENTER: selecionar  •  ESC: voltar"
        footer_surf = self.small_font.render(footer_text, True, (180, 180, 200))
        footer_rect = footer_surf.get_rect(center=(self.center_x, panel_rect.bottom - 25))
        self.screen.blit(footer_surf, footer_rect)
