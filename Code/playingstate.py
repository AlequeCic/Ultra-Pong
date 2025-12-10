import os
import threading
from settings import *
from player import *
from inputhandler import *
from world import *
from gamestate import BaseState, StateID
from network.network_handler import NetworkHandler
from network.network_input import NetworkInputHandler
from menu_state.pause import *


def _safe_disconnect(net):
    try:
        if net is None:
            return
        if hasattr(net, "disconnect_clean"):
            net.disconnect_clean()
        else:
            net.disconnect()
    except Exception as e:
        print(f"[PlayingState] async disconnect error: {e}")

class PlayingState(BaseState):
    FIXED_DT = 1/FPS

    def __init__(self, state_manager):
        super().__init__(state_manager)
        
        self.world = None  # World variables for net
        self.accumulator = 0.0
        self.all_sprites = None
        self.paddle_sprites = None
        self.players = {}
        self.ball = None
        self.game_mode = "local"
        self.network = None

        # Disconnect handling
        self.opponent_disconnected = False
        self.disconnect_timer = 0.0
        self.disconnect_message_duration = 3.0  # Show message for 3 seconds before returning to menu

        self.pause_notice_timer = 0.0

        #fonts
        # --- Controle de pausa / menu in-game ---
        self.paused = False
        self.pause_options = ["Resume", "Main Menu", "Quit"]
        self.pause_index = 0
        self.last_pause_state = False # detect changes
        self.pause_initiator = None
        self.pause_notice = ""
        self.pause_dots = ""
        self.dot_timer = 0.0
        self.dot_interval = 0.5  # segundos

        # fontes principais
        self.score_font = pygame.font.Font(None, 80)
        self.countdown_font = pygame.font.Font(None, 140)

        # debug
        self.frame_times = []
        self.max_frame_samples = 240
        self.last_substeps = 0
        self.debug_font = pygame.font.Font(None, 24)

        # fontes do menu de pausa
        font_path = "8-BIT WONDER.TTF"
        if os.path.exists(font_path):
            self.pause_title_font = pygame.font.Font(font_path, 56)
            self.pause_option_font = pygame.font.Font(font_path, 28)
            self.pause_small_font = pygame.font.Font(font_path, 18)
        else:
            self.pause_title_font = pygame.font.Font(None, 56)
            self.pause_option_font = pygame.font.Font(None, 28)
            self.pause_small_font = pygame.font.Font(None, 18)

        # cores para o menu de pausa 
        self.pause_panel_color = (10, 10, 10)
        self.pause_panel_border = (200, 200, 200)
        self.pause_text_color = (230, 230, 240)
        self.pause_highlight_color = (55, 255, 139)  

    def enter(self, game_mode="local", network = None):
        # pygame.mouse.set_visible(False)
        self.game_mode = game_mode
        self.network = network

        # reset de pausa ao entrar no jogo
        self.paused = False
        self.pause_index = 0
        
        # reset disconnect state
        self.opponent_disconnected = False
        self.disconnect_timer = 0.0

        #pause
        self.pause_notice = ""
        self.last_pause_state = False

        # initializing world variables
        self.world = World()
        self.accumulator = 0.0

        # initializing sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.paddle_sprites = pygame.sprite.Group()

        # players config
        self.setup_players()

        #ball creation
        self.ball = Ball(self.all_sprites, self.paddle_sprites, self.update_score)


    def exit(self):
        # ending network
        if self.network:
            try:
                self.network.disconnect_clean()
            except Exception as e:
                print(f"[PlayingState] exit disconnect error: {e}")
            finally:
                self.network = None
    
    def setup_players(self):
        # singleplayer (TODO)

        # local coop (sem IA por enquanto)
        if self.game_mode == "local":
            # player 1
            p1_controller = InputHandler(pygame.K_w, pygame.K_s)
            self.players['player1'] = Player(
                "TEAM_1",
                p1_controller,
                (self.all_sprites, self.paddle_sprites)
            )
            
            # player 2
            p2_controller = InputHandler(pygame.K_UP, pygame.K_DOWN)
            self.players['player2'] = Player(
                "TEAM_2",
                p2_controller,
                (self.all_sprites, self.paddle_sprites)
            )
            
        # multiplayer 1v1
        elif self.game_mode == "multiplayer_1v1" and self.network:
            # Multiplayer via rede
            local_keys = (pygame.K_w, pygame.K_s)
            local_controller = InputHandler(*local_keys)
            remote_controller = NetworkInputHandler(self.network)
            
            if self.network.player_id == 1:
                # Jogador 1 é local
                self.players['player1'] = Player("TEAM_1", local_controller,
                                                (self.all_sprites, self.paddle_sprites))
                self.players['player2'] = Player("TEAM_2", remote_controller,
                                                (self.all_sprites, self.paddle_sprites))
            else:
                # Jogador 2 é local
                self.players['player1'] = Player("TEAM_1", remote_controller,
                                                (self.all_sprites, self.paddle_sprites))
                self.players['player2'] = Player("TEAM_2", local_controller,
                                                (self.all_sprites, self.paddle_sprites))
        
        elif self.game_mode == "multiplayer_2v2":
            pass  # Implementação futura


    def handle_events(self, events):

        if self.opponent_disconnected:
            return
        
        # Se está pausado e SOMOS NÓS que pausamos, processa menu
        if self.paused and self.pause_initiator == "local":
            self._handle_pause_events(events)
            return
        
        # Se está pausado pelo oponente, não processa nada (não pode despausar)
        if self.paused and self.pause_initiator == "remote":
            return

        # jogo normal: ESC entra em pausa
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._toggle_pause_local()
                self.pause_index = 0
                return
            
    def _toggle_pause_local(self):
        """Alterna pausa localmente e notifica rede"""
        new_pause_state = not self.paused
        self.paused = new_pause_state
        self.pause_initiator = "local" if new_pause_state else None
        
        # Notificar rede
        if self.network and new_pause_state:
            self.network.send_pause_request(new_pause_state)

    def _handle_pause_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.pause_index = (self.pause_index - 1) % len(self.pause_options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.pause_index = (self.pause_index + 1) % len(self.pause_options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._activate_pause_option()
                elif event.key == pygame.K_ESCAPE:
                    # ESC dentro do pause volta direto ao jogo (apenas se for nosso pause)
                    if self.pause_initiator == "local":
                        self._set_pause(False, initiator="local")

    def _activate_pause_option(self):
        option = self.pause_options[self.pause_index]

        if option == "Resume":
            # Apenas o iniciador local pode despausar
            if self.pause_initiator == "local":
                self._set_pause(False, initiator="local")
            
            # Se for pausa remota, não faz nada (o menu não deve aparecer mesmo)

        elif option == "Main Menu":
            # Primeiro desconecta da rede
            if self.network:
                # Desconexão assíncrona para não travar a UI
                net = self.network
                self.network = None
                threading.Thread(target=lambda: _safe_disconnect(net), daemon=True).start()

            # Retorna ao menu principal
            self.state_manager.change_state(StateID.MAIN_MENU)

        elif option == "Quit":
            self.state_manager.quit()

    def update_score(self, side):
        self.world.score[side] += 1
        self.world.start_countdown(3.0, FPS)  # 3 seconds

        if self.ball:
            # put the ball in the middle and randomize its direction
            self.ball.reset()

    def display_score(self):
        # team_1
        team_1_surf = self.score_font.render(
            str(self.world.score['TEAM_1']), True, OBJECTS_COLORS['TEAM_1']
        )
        team_1_rect = team_1_surf.get_frect(
            center=(WINDOW_WIDTH/2 - WINDOW_WIDTH/4, 40)
        )
        self.screen.blit(team_1_surf, team_1_rect)

        # team_2
        team_2_surf = self.score_font.render(
            str(self.world.score['TEAM_2']), True, OBJECTS_COLORS['TEAM_2']
        )
        team_2_rect = team_2_surf.get_frect(
            center=(WINDOW_WIDTH/2 + WINDOW_WIDTH/4, 40)
        )
        self.screen.blit(team_2_surf, team_2_rect)

    def display_countdown(self):
        if not self.world:
            return

        # countdown de despausa
        if self.world.phase == "pause_countdown":
            if self.world.pause_countdownEndTick is not None:
                remaining_ticks = self.world.pause_countdownEndTick - self.world.tick
                secs_left = remaining_ticks / FPS
                countdown_value = int(secs_left) + 1
                
                # Desenhar
                countdown_surf = self.countdown_font.render(str(countdown_value), True, "yellow")
                countdown_rect = countdown_surf.get_frect(
                    center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2 - 80)
                )
                self.screen.blit(countdown_surf, countdown_rect)
                
                # Mensagem
                resume_text = "Game resuming in"
                resume_surf = self.pause_small_font.render(resume_text, True, (200, 200, 100))
                resume_rect = resume_surf.get_frect(
                    center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2 + 20)
                )
                self.screen.blit(resume_surf, resume_rect)
            return #ele nao mostra o outro contador se esse estiver aparecendo

        if not self.world.phase == "countdown":
            return

        #countdown normal
        remaining_ticks = self.world.countdownEndTick - self.world.tick
        secs_left = remaining_ticks / FPS
        countdown_value = int(secs_left) + 1

        # drawing
        countdown_surf = self.countdown_font.render(str(countdown_value), True, "white")
        countdown_rect = countdown_surf.get_frect(
            center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2 - 80)
        )

        # pulsing effect (pode ser implementado depois)
        self.screen.blit(countdown_surf, countdown_rect)

    def display_debug(self):
        pass

    def draw(self):
        self.screen.fill("black")
        # line in the middle
        pygame.draw.line(
            self.screen,
            '#262626',
            (WINDOW_WIDTH/2, 0),
            (WINDOW_WIDTH/2, WINDOW_HEIGHT),
            8
        )

        if self.ball:
            self.ball.draw_trail(self.screen)
        if self.all_sprites:
            self.all_sprites.draw(self.screen)

        # ui
        self.display_score()
        self.display_countdown()

        # debug
        if self.frame_times:
            self.display_debug()

        # overlay de pause por cima de tudo
        if self.paused and self.pause_initiator == "local":
            self._draw_pause_menu()

        #pause notification
        elif self.paused and self.pause_initiator == "remote":
            self._draw_remote_pause_message()
        
        # overlay de desconexão
        if self.opponent_disconnected:
            self._draw_disconnect_message()

    def _draw_disconnect_message(self):
        """Draw overlay when opponent disconnects"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2

        msg_text = "OPPONENT DISCONNECTED"
        msg_surf = self.pause_title_font.render(msg_text, True, (255, 100, 100))
        msg_rect = msg_surf.get_rect(center=(center_x, center_y - 20))
        self.screen.blit(msg_surf, msg_rect)

        remaining = max(0, self.disconnect_message_duration - self.disconnect_timer)
        sub_text = f"Returning to menu in {int(remaining) + 1}..."
        sub_surf = self.pause_small_font.render(sub_text, True, (180, 180, 200))
        sub_rect = sub_surf.get_rect(center=(center_x, center_y + 30))
        self.screen.blit(sub_surf, sub_rect)
    
    def _draw_pause_menu(self):
        # overlay escuro
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # preto com alpha um pouco mais forte
        self.screen.blit(overlay, (0, 0))

        panel_width = 520
        panel_height = 280
        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2

        panel_rect = pygame.Rect(
            center_x - panel_width // 2,
            center_y - panel_height // 2,
            panel_width,
            panel_height,
        )

        # painel 
        pygame.draw.rect(self.screen, self.pause_panel_color, panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, self.pause_panel_border, panel_rect, width=2, border_radius=16)

        # título
        title_text = "PAUSED"
        shadow_surf = self.pause_title_font.render(title_text, True, (0, 0, 0))
        title_surf = self.pause_title_font.render(title_text, True, self.pause_text_color)

        title_rect = title_surf.get_rect(center=(center_x, panel_rect.top + 60))
        shadow_rect = shadow_surf.get_rect(center=(center_x + 3, panel_rect.top + 63))

        self.screen.blit(shadow_surf, shadow_rect)
        self.screen.blit(title_surf, title_rect)

        
        bar_width = 140
        bar_height = 6
        bar_rect = pygame.Rect(
            center_x - bar_width // 2,
            title_rect.bottom + 8,
            bar_width,
            bar_height
        )
        pygame.draw.rect(self.screen, (220, 220, 220), bar_rect)

        # opções
        start_y = title_rect.bottom + 35
        spacing = 40

        for i, text in enumerate(self.pause_options):
            y = start_y + i * spacing
            selected = (i == self.pause_index)
            color = self.pause_highlight_color if selected else self.pause_text_color

            option_surf = self.pause_option_font.render(text, True, color)
            option_rect = option_surf.get_rect(center=(center_x, y))
            self.screen.blit(option_surf, option_rect)

            if selected:
                # cursor 
                cursor_height = option_rect.height - 6
                cursor_rect = pygame.Rect(
                    option_rect.left - 26,
                    option_rect.centery - cursor_height // 2,
                    10,
                    cursor_height
                )
                pygame.draw.rect(self.screen, self.pause_highlight_color, cursor_rect, border_radius=3)

    def _draw_remote_pause_message(self):
        """Desenha mensagem quando o oponente pausou"""
        # overlay escuro
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2

        # Painel similar ao do menu de pausa
        panel_width = 520
        panel_height = 200
        panel_rect = pygame.Rect(
            center_x - panel_width // 2,
            center_y - panel_height // 2,
            panel_width,
            panel_height,
        )

        # Painel 
        pygame.draw.rect(self.screen, self.pause_panel_color, panel_rect, border_radius=16)
        pygame.draw.rect(self.screen, self.pause_panel_border, panel_rect, width=2, border_radius=16)

        # Título
        title_text = "GAME PAUSED"
        title_surf = self.pause_title_font.render(title_text, True, self.pause_text_color)
        title_rect = title_surf.get_rect(center=(center_x, panel_rect.top + 60))
        self.screen.blit(title_surf, title_rect)

        # Mensagem maior com cor destacada
        msg_text = "Opponent paused the game"
        msg_surf = self.pause_option_font.render(msg_text, True, self.pause_highlight_color)
        msg_rect = msg_surf.get_rect(center=(center_x, center_y))
        self.screen.blit(msg_surf, msg_rect)

        # Mensagem de instrução
        instr_text = "Waiting for opponent to resume" + self.pause_dots
        instr_surf = self.pause_small_font.render(instr_text, True, self.pause_text_color)
        instr_rect = instr_surf.get_rect(center=(center_x, center_y + 40))
        self.screen.blit(instr_surf, instr_rect)


    def update(self, dt):
        #update network
        if self.network:
            self.network.update()
            self._sync_pause_from_network()
            self._send_local_input()

        start_ticks = pygame.time.get_ticks()
        self.last_substeps = self.fixed_step(dt)  # returns substeps
        frame_ms = pygame.time.get_ticks() - start_ticks
        self.frame_times.append(frame_ms)
        if len(self.frame_times) > self.max_frame_samples:
            self.frame_times.pop(0)

    def fixed_step(self, dt, max_substeps=10):
        """this function accumulates time and runs simulation in the world"""
        step_dt = self.FIXED_DT
        self.accumulator += dt

        # clamping acc for huge accumulations
        if self.accumulator > max_substeps * step_dt:
            self.accumulator = max_substeps * step_dt
        
        # verifying fps
        substeps = 0
        while self.accumulator >= self.FIXED_DT and substeps < max_substeps:
            self.world.tick += 1

            # launch ball after countdown ends
            if self.world.maybe_resume() and self.ball:
                self.ball.launch_after_countdown()

            # update sprites
            self.all_sprites.update(self.FIXED_DT)

            # consume one step
            self.accumulator -= self.FIXED_DT
            substeps += 1

        return substeps

        '''
        TO TRY LATER (it freezes the ball and the trail)
        # after countdown enter playing phase
        if self.world.phase == "play":
            self.all_sprites.update(self.FIXED_DT)
        
        else:
            # only players are updated in countdown
            for sprite in self.all_sprites:
                if not isinstance(sprite, Ball):  # finds if it isn't the ball
                    sprite.update(self.FIXED_DT)
        '''

    #metodos de rede
    def _send_local_input(self):
        if not self.network:
            return
        
        is_host = self.network.is_host()

        local_player_key = 'player1' if self.network.player_id == 1 else 'player2'
        if local_player_key in self.players:
            player = self.players[local_player_key]
            if hasattr(player.input_handler, 'get_direction'):
                direction = player.input_handler.get_direction()
                self.network.send_input(direction)
        
        # Host envia estado do jogo
        if is_host and self.ball:
            game_state ={
                'ball_x': self.ball.rect.centerx,
                'ball_y': self.ball.rect.centery,
                'ball_dx': self.ball.direction.x,
                'ball_dy': self.ball.direction.y,
                'ball_speed': self.ball.speed,
                'score_t1': self.world.score['TEAM_1'],
                'score_t2': self.world.score['TEAM_2'],
                'phase': self.world.phase,
                'tick': self.world.tick,
                'countdown_end': self.world.countdownEndTick
            }
        
            self.network.send_game_state(game_state)
            #print(f"[PlayingState] Host sending game_state: ball=({game_state['ball_x']}, {game_state['ball_y']}), score=({game_state['score_t1']}, {game_state['score_t2']})")
        
        # Cliente aplica estado recebido
        if not is_host:
            self._apply_game_state()

    def _apply_game_state(self):
        if not self.network or not self.ball:
            return
        
        state = self.network.get_game_state()
        if not state:
            return
        
        #print(f"[PlayingState] Applying game_state: ball=({state.get('ball_x')}, {state.get('ball_y')}), score=({state.get('score_t1')}, {state.get('score_t2')})")
        

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

    def _set_pause(self, paused: bool, initiator: str = "local"):
        """Define estado de pausa e notifica rede se necessário"""
        # Se o estado não mudou, não faz nada
        if self.paused == paused and self.pause_initiator == initiator:
            return
        
        self.paused = paused
        self.pause_initiator = initiator if paused else None
        self.pause_dots = ""
        self.dot_timer = 0.0
        
        # Se estamos despausando: só cria pause_countdown se estávamos jogando;
        # se estávamos em countdown de gol, apenas retoma o countdown existente.
        if not paused and self.world:
            if self.world.phase == "play":
                self.world.start_pause_countdown(3.0, FPS)
            elif self.world.phase == "countdown":
                self.world.start_countdown(3.0, FPS)
        
        # Notificar rede se for ação local
        if initiator == "local" and self.network:
            self.network.send_pause_request(paused)

    def _sync_pause_from_network(self):
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
                    self._set_pause(True, initiator="remote")
                else:
                    # Recebeu despausa do oponente - iniciar countdown
                    self._set_pause(False, initiator="remote")

    def update_dot_animation(self, dt):
        if self.paused:
            self.dot_timer += dt
        if self.dot_timer >= self.dot_interval:
            self.dot_timer = 0
            self.pause_dots = "." if len(self.pause_dots) >= 3 else self.pause_dots + "."


# feito por ia, pra debugar o fps (adicionei o Pause aq)
import time as _time_hr
def _ps_update_hr(self, dt):
    if not hasattr(self, 'last_dt'):
        self.last_dt = 0.0

    # Check for opponent disconnect
    if getattr(self, 'network', None) and not self.opponent_disconnected:
        if not self.network.is_opponent_connected():
            self.opponent_disconnected = True
            self.disconnect_timer = 0.0
            print("[PlayingState] Opponent disconnected!")
    
    # Handle disconnect timer - return to menu after delay
    if self.opponent_disconnected:
        self.disconnect_timer += dt
        if self.disconnect_timer >= self.disconnect_message_duration:
            if self.network:
                self.network.disconnect()
            self.state_manager.change_state(StateID.MAIN_MENU)
        return  # Don't update game while showing disconnect message

    self.update_dot_animation(dt)

    # Atualiza rede primeiro
    if getattr(self, 'network', None):
        self.network.update()
        self._sync_pause_from_network()  
        self._send_local_input()

    # Se estiver em countdown de pausa, atualizar o tick
    if self.world and self.world.phase == "pause_countdown":
        # Atualiza o tick para o countdown funcionar
        self.world.tick += 1
        
        # Verificar se o countdown terminou
        if self.world.maybe_resume():
            # Countdown terminou, despausar completamente
            self.paused = False
            self.pause_initiator = None
            self.pause_dots = ""
            # Notificar rede se somos o host/local que iniciou o despause
            if self.pause_initiator == "local" and self.network:
                self.network.send_pause_request(False)
        return

    # se estiver pausado, não avança simulação
    if self.paused:
        self.last_dt = 0.0
        return

    self.last_dt = dt 
    start_time = _time_hr.perf_counter()
    self.last_substeps = self.fixed_step(dt)
    frame_ms = (_time_hr.perf_counter() - start_time) * 1000.0
    self.frame_times.append(frame_ms)
    if len(self.frame_times) > self.max_frame_samples:
        self.frame_times.pop(0)

PlayingState.update = _ps_update_hr

