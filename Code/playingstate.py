import os
import threading
import time as _time_hr
from settings import *
from player import *
from inputhandler import *
from world import *
from gamestate import BaseState, StateID
from networksync import *
from menu_state.pause import *
from menu_state.ui import *

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
        self.network_sync = None  # Será inicializado em enter()
        self.pause_manager = None  # Será inicializado em enter()

        # Disconnect handling
        self.opponent_disconnected = False
        self.disconnect_timer = 0.0
        self.disconnect_message_duration = 3.0  # Show message for 3 seconds before returning to menu

        # Pause control - managed by PauseManager (single source of truth)
        # Use self._get_pause_state() to access current pause state

        # debug
        self.frame_times = []
        self.max_frame_samples = 240
        self.last_substeps = 0
        self.last_dt = 0.0
        self.debug_font = pygame.font.Font(None, 24)

        # fontes do menu de pausa
        font_path = "8-BIT WONDER.TTF"
        if os.path.exists(font_path):
            pause_title_font = pygame.font.Font(font_path, 56)
            pause_option_font = pygame.font.Font(font_path, 28)
            pause_small_font = pygame.font.Font(font_path, 18)
        else:
            pause_title_font = pygame.font.Font(None, 56)
            pause_option_font = pygame.font.Font(None, 28)
            pause_small_font = pygame.font.Font(None, 18)

        # Instanciar as classes de UI
        self.pause_menu = PauseMenu(self.screen, pause_title_font, pause_option_font, pause_small_font)
        self.remote_pause_msg = RemotePauseMessage(self.screen, pause_title_font, pause_option_font, pause_small_font)
        self.disconnect_msg = DisconnectMessage(self.screen, pause_title_font, pause_small_font)
        self.countdown_display = CountdownDisplay(self.screen, None)  # world será setado em enter()
        self.score_display = ScoreDisplay(self.screen, None)  # world será setado em enter()

    def enter(self, game_mode="local", network = None):
        # pygame.mouse.set_visible(False)
        self.game_mode = game_mode
        self.network = network

        # reset pause menu UI
        self.pause_menu.reset()
        if self.pause_manager:
            self.pause_manager.reset()
        
        # reset disconnect state
        self.opponent_disconnected = False
        self.disconnect_timer = 0.0

        #pause
        self.pause_notice = ""
        self.last_pause_state = False

        # initializing world variables
        self.world = World()
        self.countdown_display.world = self.world  # Setar world no countdown_display
        self.score_display.world = self.world  # Setar world no score_display
        
        # Inicializar managers
        self.pause_manager = PauseManager(self.network, self.world)
        self.accumulator = 0.0

        # initializing sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.paddle_sprites = pygame.sprite.Group()

        # players config
        self.setup_players()

        #ball creation
        self.ball = Ball(self.all_sprites, self.paddle_sprites, self.update_score)
        
        # Inicializar NetworkSync
        self.network_sync = NetworkSync(self.network, self.ball, self.world, self.players)


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
        
        # Get current pause state from manager
        paused, initiator = self._get_pause_state()
        
        # Se está pausado e SOMOS NÓS que pausamos, processa menu
        if paused and initiator == "local":
            selected_option = self.pause_menu.handle_events(events)
            if selected_option:
                self._activate_pause_option(selected_option)
            return
        
        # Se está pausado pelo oponente, não processa nada (não pode despausar)
        if paused and initiator == "remote":
            return

        # jogo normal: ESC entra em pausa
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._toggle_pause_local()
                return
            
    def _toggle_pause_local(self):
        """Alterna pausa localmente e notifica rede"""
        if self.pause_manager:
            self.pause_manager.toggle_pause_local()

    def _activate_pause_option(self, option):
        if option == "Resume":
            # Apenas o iniciador local pode despausar
            paused, initiator = self._get_pause_state()
            if initiator == "local":
                self._set_pause(False, initiator="local")
            
            # Se for pausa remota, não faz nada (o menu não deve aparecer mesmo)

        elif option == "Main Menu":
            # Primeiro desconecta da rede
            if self.network:
                # Desconexão assíncrona para não travar a UI
                net = self.network
                self.network = None
                threading.Thread(target=lambda: net.disconnect(), daemon=True).start()

            # Retorna ao menu principal
            self.state_manager.change_state(StateID.MAIN_MENU)

        elif option == "Quit":
            self.state_manager.quit()

    def update_score(self, side):
        if self.score_display:
            self.score_display.update_score(side)
        if self.ball:
            # put the ball in the middle and randomize its direction
            self.ball.reset()

    def display_score(self):
        if self.score_display:
            self.score_display.draw()


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
        self.countdown_display.update()
        self.countdown_display.draw()

        # debug
        if self.frame_times:
            self.display_debug()

        center_x = WINDOW_WIDTH // 2
        center_y = WINDOW_HEIGHT // 2

        # Get current pause state from manager (single source of truth)
        paused, initiator = self._get_pause_state()
        
        # overlay de pause por cima de tudo
        if paused and initiator == "local":
            self.pause_menu.draw(center_x, center_y)

        #pause notification
        elif paused and initiator == "remote":
            self.remote_pause_msg.draw(center_x, center_y)
        
        # overlay de desconexão
        if self.opponent_disconnected:
            self.disconnect_msg.draw(center_x, center_y, self.disconnect_timer, self.disconnect_message_duration)

    def update(self, dt):
        # Check for opponent disconnect
        if self.network and not self.opponent_disconnected:
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
        
        # Update dot animation for remote pause message
        self.update_dot_animation(dt)
        
        # Update network
        if self.network:
            self.network.update()
            self._sync_pause_from_network()
            self._send_local_input()
        
        # Se estiver em countdown de pausa, atualizar o tick
        if self.world and self.world.phase == "pause_countdown":
            # Atualiza o tick para o countdown funcionar
            self.world.tick += 1
            
            # Verificar se o countdown terminou
            if self.world.maybe_resume():
                # Countdown terminou - forçar despause sem rearmar countdown
                if self.pause_manager:
                    # Apenas resetar o estado interno sem chamar set_pause
                    # (que tentaria criar outro countdown)
                    self.pause_manager.paused = False
                    self.pause_manager.pause_initiator = None
            return
        
        # Se estiver pausado, não avança simulação
        paused, _ = self._get_pause_state()
        if paused:
            self.last_dt = 0.0
            return
        
        # Avança simulação normalmente
        self.last_dt = dt
        #start_time = _time_hr.perf_counter()
        self.last_substeps = self.fixed_step(dt)
        #frame_ms = (_time_hr.perf_counter() - start_time) * 1000.0
        #self.frame_times.append(frame_ms)
        #if len(self.frame_times) > self.max_frame_samples:
            #self.frame_times.pop(0)

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

    #metodos de rede
    def _send_local_input(self):
        if self.network_sync:
            self.network_sync.send_local_input()

    def _apply_game_state(self):
        if self.network_sync:
            self.network_sync.apply_game_state()

    def _set_pause(self, paused: bool, initiator: str = "local"):
        """Define estado de pausa e notifica rede se necessário"""
        if self.pause_manager:
            self.pause_manager.set_pause(paused, initiator)
            # State is now retrieved via _get_pause_state()

    def _sync_pause_from_network(self):
        """Sincroniza pausa com a rede"""
        if self.pause_manager:
            self.pause_manager.sync_pause_from_network()
            # State is now retrieved via _get_pause_state()

    def _get_pause_state(self):
        """Get current pause state from PauseManager (single source of truth)"""
        if self.pause_manager and hasattr(self.pause_manager, "paused"):
            return self.pause_manager.paused, getattr(self.pause_manager, "pause_initiator", None)
        return False, None
    
    def update_dot_animation(self, dt):
        paused, initiator = self._get_pause_state()
        if paused and initiator == "remote":
            self.remote_pause_msg.update_dot_animation(dt)



