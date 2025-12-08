from settings import *
from player import *
from inputhandler import *
from world import *
from gamestate import BaseState
from network.network_handler import NetworkHandler
from network.network_input import NetworkInputHandler

class PlayingState(BaseState):
    FIXED_DT = 1/FPS

    def __init__(self, state_manager):
        super().__init__(state_manager)
        
        self.world = None #World variables for net
        self.accumulator = 0.0
        self.all_sprites = None
        self.paddle_sprites = None
        self.players = {}
        self.ball = None
        self.game_mode = "local"
        self.network: NetworkHandler | None = None

        #fonts
        self.score_font = pygame.font.Font(None, 80)
        self.countdown_font = pygame.font.Font(None, 140)

        #debuggin
        self.frame_times = []
        self.max_frame_samples = 240
        self.last_substeps = 0
        self.debug_font = pygame.font.Font(None, 24)

    def enter(self, game_mode="local", network=None):
        self.game_mode = game_mode
        self.network = network

        self.world = World()
        self.accumulator = 0.0

        self.all_sprites = pygame.sprite.Group()
        self.paddle_sprites = pygame.sprite.Group()

        self.setup_players()

        self.ball = Ball(self.all_sprites, self.paddle_sprites, self.update_score)
    
    def setup_players(self):
        if self.game_mode == "local":
            p1_controller = InputHandler(pygame.K_w, pygame.K_s)
            self.players['player1'] = Player("TEAM_1", 
                                             p1_controller, 
                                             (self.all_sprites, self.paddle_sprites))
            
            p2_controller = InputHandler(pygame.K_UP, pygame.K_DOWN)
            self.players['player2'] = Player("TEAM_2",
                                            p2_controller,
                                            (self.all_sprites, self.paddle_sprites))
            
        elif self.game_mode == "multiplayer_1v1" and self.network:
            local_keys = (pygame.K_w, pygame.K_s)
            local_controller = InputHandler(*local_keys)
            remote_controller = NetworkInputHandler(self.network)
            
            if self.network.player_id == 1:
                self.players['player1'] = Player("TEAM_1", local_controller,
                                                (self.all_sprites, self.paddle_sprites))
                self.players['player2'] = Player("TEAM_2", remote_controller,
                                                (self.all_sprites, self.paddle_sprites))
            else:
                self.players['player1'] = Player("TEAM_1", remote_controller,
                                                (self.all_sprites, self.paddle_sprites))
                self.players['player2'] = Player("TEAM_2", local_controller,
                                                (self.all_sprites, self.paddle_sprites))

    def handle_events(self, events):
        #TODO
        pass

    def update_score(self, side):
        self.world.score[side] += 1
        self.world.start_countdown(3.0, FPS) # 3 seconds

        if self.ball:
            self.ball.reset() #put the ball in the middle and randomize its direction

    def display_score(self):
        #team_1
        team_1_surf = self.score_font.render(str(self.world.score['TEAM_1']), True, OBJECTS_COLORS['TEAM_1'])
        team_1_rect = team_1_surf.get_frect(center = (WINDOW_WIDTH/2 - WINDOW_WIDTH/4, 40))
        self.screen.blit(team_1_surf, team_1_rect)
        #team_2
        team_2_surf = self.score_font.render(str(self.world.score['TEAM_2']), True, OBJECTS_COLORS['TEAM_2'])
        team_2_rect = team_2_surf.get_frect(center = (WINDOW_WIDTH/2 + WINDOW_WIDTH/4, 40))
        self.screen.blit(team_2_surf, team_2_rect)

    def display_countdown(self):
        if not self.world or self.world.phase != "countdown":
            return

        remaining_ticks = self.world.countdownEndTick - self.world.tick
        secs_left = remaining_ticks/FPS
        countdown_value = int(secs_left) + 1

        #drawing
        countdown_surf = self.countdown_font.render(str(countdown_value), True, "white")
        countdown_rect = countdown_surf.get_frect(center = (WINDOW_WIDTH/2, WINDOW_HEIGHT/2 - 80))

        #pulsing effect

        self.screen.blit(countdown_surf,countdown_rect)

    def display_debug(self):
        last_ms = self.frame_times[-1]
        avg_ms = sum(self.frame_times) / len(self.frame_times)
        worst_ms = max(self.frame_times)
        fps_now = (1.0 / self.last_dt) if self.last_dt > 0 else 0.0
        fps_avg = 1000.0 / avg_ms if avg_ms > 0 else 0.0
        text = (f"FPS:{fps_now:.1f} AVG:{fps_avg:.1f}\nWORST:{worst_ms:.2f}ms "
                f"SUB:{self.last_substeps} ACC:{self.accumulator:.4f} \n"
                f"TICK:{self.world.tick if self.world else 0}")
        surf = self.debug_font.render(text, True, (180,180,180))
        self.screen.blit(surf, (8, WINDOW_HEIGHT - 68))

    def draw(self):
        self.screen.fill("black")
        #line in the middle
        pygame.draw.line(self.screen, '#262626', (WINDOW_WIDTH/2, 0), (WINDOW_WIDTH/2, WINDOW_HEIGHT), 8)

        if self.ball:
            self.ball.draw_trail(self.screen)
        if self.all_sprites:
            self.all_sprites.draw(self.screen)

        #ui
        self.display_score()
        self.display_countdown()

        #debug
        if self.frame_times:
            self.display_debug()
    
    def update(self, dt):
        
        start_ticks = pygame.time.get_ticks()
        self.last_substeps = self.fixed_step(dt)  # returns substeps
        frame_ms = pygame.time.get_ticks() - start_ticks
        self.frame_times.append(frame_ms)
        if len(self.frame_times) > self.max_frame_samples:
            self.frame_times.pop(0)

    def fixed_step(self, dt, max_substeps=10):
        '''this function accumulates time and run simulation in the world'''
        step_dt = self.FIXED_DT
        self.accumulator +=dt

        if self.accumulator > max_substeps * step_dt:
            self.accumulator = max_substeps * step_dt
        
        if self.network:
            self.network.update()
            self._send_local_input()
        
        substeps = 0
        while self.accumulator >= self.FIXED_DT and substeps < max_substeps :
            self.world.tick += 1

            if self.world.maybe_resume() and self.ball:
                self.ball.launch_after_countdown()

            self.all_sprites.update(self.FIXED_DT)

            self.accumulator -= self.FIXED_DT
            substeps+=1

        return substeps
    
    def _send_local_input(self):
        if not self.network:
            return
        
        local_player_key = 'player1' if self.network.player_id == 1 else 'player2'
        if local_player_key in self.players:
            player = self.players[local_player_key]
            if hasattr(player.input_handler, 'get_direction'):
                direction = player.input_handler.get_direction()
                self.network.send_input(direction)
        
        if self.network.is_host() and self.ball:
            self.network.send_game_state({
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
            })
        
        if not self.network.is_host():
            self._apply_game_state()
    
    def _apply_game_state(self):
        if not self.network or not self.ball:
            return
        
        state = self.network.get_game_state()
        if not state:
            return
        
        if 'ball_x' in state:
            lerp = 0.4
            target_x = state['ball_x']
            target_y = state['ball_y']
            self.ball.rect.centerx += (target_x - self.ball.rect.centerx) * lerp
            self.ball.rect.centery += (target_y - self.ball.rect.centery) * lerp
            self.ball.direction.x = state['ball_dx']
            self.ball.direction.y = state['ball_dy']
            self.ball.speed = state['ball_speed']
        
        if 'score_t1' in state:
            self.world.score['TEAM_1'] = state['score_t1']
            self.world.score['TEAM_2'] = state['score_t2']
        
        if 'phase' in state:
            self.world.phase = state['phase']
            self.world.tick = state.get('tick', self.world.tick)
            self.world.countdownEndTick = state.get('countdown_end')

        '''
        TO TRY LATER (it freezes the ball and the trail)
        #after countdown enter playing phase
        if self.world.phase == "play":
            self.all_sprites.update(self.FIXED_DT)
        
        else:
            #only players are updated in countdown
            for sprite in self.all_sprites:
                if not isinstance(sprite, Ball): #finds if it isn't the ball
                    sprite.update(self.FIXED_DT)'''

 # feito por ia, pra debugar o fps
import time as _time_hr
def _ps_update_hr(self, dt):
    if not hasattr(self, 'last_dt'):
        self.last_dt = 0.0
    self.last_dt = dt
    start_time = _time_hr.perf_counter()
    self.last_substeps = self.fixed_step(dt)
    frame_ms = (_time_hr.perf_counter() - start_time) * 1000.0
    self.frame_times.append(frame_ms)
    if len(self.frame_times) > self.max_frame_samples:
        self.frame_times.pop(0)
PlayingState.update = _ps_update_hr