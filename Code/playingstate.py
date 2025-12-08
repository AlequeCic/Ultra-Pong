from settings import *
from player import *
from inputhandler import *
from world import *
from gamestate import BaseState
from audio_manager import get_audio_manager

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

        #fonts
        self.score_font = pygame.font.Font(None, 80)
        self.countdown_font = pygame.font.Font(None, 140)

        #debuggin
        self.frame_times = []
        self.max_frame_samples = 240
        self.last_substeps = 0
        self.debug_font = pygame.font.Font(None, 24)

    def enter(self, game_mode="local"):
        #pygame.mouse.set_visible(False)
        self.game_mode = game_mode
        
        # Start gameplay music
        get_audio_manager().play_gameplay_music(intensity="normal", fade_ms=500)

        #initializing world variables
        self.world = World()
        self.accumulator = 0.0
        
        self.last_countdown_beep = None

        #initializing sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.paddle_sprites = pygame.sprite.Group()

        #players config
        self.setup_players()

        self.ball = Ball(self.all_sprites, self.paddle_sprites, self.on_goal_scored)

        self.ball.reset()
        self.world.start_countdown(3.0, FPS)  # 3 second countdown

    
    def setup_players(self):
        #singleplayer (TODO)

        #local coop (i don't want to make an ai for this game rn)
        if self.game_mode == "local":
            #player 1
            p1_controller = InputHandler(pygame.K_w, pygame.K_s)
            self.players['player1'] = Player("TEAM_1", 
                                             p1_controller, 
                                             (self.all_sprites, self.paddle_sprites))
            
            #player 2
            p2_controller = InputHandler(pygame.K_UP, pygame.K_DOWN)
            self.players['player2'] = Player("TEAM_2",
                                            p2_controller,
                                            (self.all_sprites, self.paddle_sprites))
            
        #multiplayer 1v1 TODO
        elif self.game_mode == "multiplayer_1v1":
            pass

    def handle_events(self, events):
        #TODO
        pass

    def on_goal_scored(self, team):
        """Callback when a goal is scored. Handles score, audio, and game state."""
        self.world.score[team] += 1
        self.world.start_countdown(3.0, FPS)
        
        # Play goal sound
        get_audio_manager().play_goal(team)
        
        #if team score >= 9 play last goal music, elif >= 6 play high intensity
        if self.world.score[team] >1:
            get_audio_manager().play_last_goal()
        elif self.world.score[team] >3:
            get_audio_manager().play_gameplay_music(intensity="high")
        
        # Reset opponent streak
        opponent = "TEAM_2" if team == "TEAM_1" else "TEAM_1"
        
        # Reset ball
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
        
        # play countdown beep sound (3, 2, 1)
        if countdown_value in [3, 2, 1]:
            if self.last_countdown_beep != countdown_value:
                get_audio_manager().play_countdown(countdown_value)
                self.last_countdown_beep = countdown_value

        #drawing
        countdown_surf = self.countdown_font.render(str(countdown_value), True, "white")
        countdown_rect = countdown_surf.get_frect(center = (WINDOW_WIDTH/2, WINDOW_HEIGHT/2 - 80))

        #pulsing effect TODO

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

        #clamping acc for huge accumulations
        if self.accumulator > max_substeps * step_dt:
            self.accumulator = max_substeps * step_dt
        
        #verifying fps
        substeps = 0
        while self.accumulator >= self.FIXED_DT and substeps < max_substeps :
            self.world.tick += 1

            #launch ball after countdown ends
            if self.world.maybe_resume() and self.ball:
                self.ball.launch_after_countdown()
                self.last_countdown_beep = None  # Reset beep tracking
                get_audio_manager().play_launch()

            #update sprites
            self.all_sprites.update(self.FIXED_DT)

            #consume one step
            self.accumulator -= self.FIXED_DT
            substeps+=1

        return substeps

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