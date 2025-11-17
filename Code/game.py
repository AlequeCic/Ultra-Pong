from settings import *
from player import *
from gamestate import *

class Game:
    def __init__(self):
        pygame.init()
        self.display = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        pygame.display.set_caption("Ultra Pong")

        #input handler
        self.input_handler = InputHandler()

        #sprites
        self.all_sprites = pygame.sprite.Group()
        self.paddle_sprites = pygame.sprite.Group()

        #game objects
        self.player1 = Player("TEAM_1", self.input_handler, (self.all_sprites, self.paddle_sprites))
        self.player2 = Player("TEAM_2", self.input_handler, (self.all_sprites, self.paddle_sprites))
        self.ball = Ball(self.all_sprites, self.paddle_sprites, self.update_score)

        #score
        self.score = {'TEAM_1': 0, 'TEAM_2': 0}
        self.countdown = 0.0
        self.counting_down = False
        self.score_font = pygame.font.Font(None, 80)
        self.countdown_font = pygame.font.Font(None, 140)

        #game states
        self.game_paused = False

    def update_game_state(self, dt):
            
            self.update_countdown(dt)
            self.all_sprites.update(dt) #updating all sprites
    

    def run(self):
        while self.running:
            #defining fps
            dt = self.clock.tick(FPS) / 1000

            #exiting the game (update in the future)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            #update
            self.update_game_state(dt) 

            #draw
            self.display.fill("Black")
            self.display_score()
            self.ball.draw_trail(self.display)
            self.all_sprites.draw(self.display) #drawing all sprites
            self.display_countdown(dt)
           

            #update method to update the screen
            pygame.display.update()
        
        #finishing the game
        pygame.quit()

    def update_countdown(self, dt):

        if self.counting_down:
            self.countdown -= dt

            #finish
            if self.countdown <= 0:
                self.counting_down = False
                self.ball.launch_after_countdown()
        
        '''
        #update only paddles:
        for sprite in self.all_sprites:
            if isinstance(sprite, Player):
                sprite.update(dt)
        '''

    def start_countdown(self):
        self.counting_down = True
        self.countdown = COUNTDOWN['ball']
        self.ball.reset()
    
    def display_countdown(self,dt):
        if not self.counting_down:
            return

        countdown_value = int(self.countdown) + 1

        #drawing
        countdown_surf = self.countdown_font.render(str(countdown_value), True, "white")
        countdown_rect = countdown_surf.get_frect(center = (WINDOW_WIDTH/2, WINDOW_HEIGHT/2 - 80))

        #pulsing effect

        self.display.blit(countdown_surf,countdown_rect)

    def update_score(self,side):
        self.score[side]  +=1
        self.start_countdown()

    def display_score(self):
        #team_1
        team_1_surf = self.score_font.render(str(self.score['TEAM_1']), True, OBJECTS_COLORS['TEAM_1'])
        team_1_rect = team_1_surf.get_frect(center = (WINDOW_WIDTH/2 - WINDOW_WIDTH/4, 40))
        self.display.blit(team_1_surf, team_1_rect)
        #team_2
        team_2_surf = self.score_font.render(str(self.score['TEAM_2']), True, OBJECTS_COLORS['TEAM_2'])
        team_2_rect = team_2_surf.get_frect(center = (WINDOW_WIDTH/2 + WINDOW_WIDTH/4, 40))
        self.display.blit(team_2_surf, team_2_rect)

        pygame.draw.line(self.display, '#262626', (WINDOW_WIDTH/2, 0), (WINDOW_WIDTH/2, WINDOW_HEIGHT), 8)

    
    
    