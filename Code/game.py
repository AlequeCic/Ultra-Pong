from settings import *
from player import *

class Game:
    def __init__(self):
        pygame.init()
        self.display = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        pygame.display.set_caption("Ultra Pong")

        #sprites
        self.all_sprites = pygame.sprite.Group()
        self.paddle_sprites = pygame.sprite.Group()

        #game objects
        self.player1 = Player("TEAM_1", (self.all_sprites, self.paddle_sprites))
        self.ball = Ball(self.all_sprites, self.paddle_sprites)

        #score
        self.score = {'TEAM_1': 0, 'TEAM_2': 0}

    def run(self):
        while self.running:
            #defining fps
            dt = self.clock.tick(FPS) / 1000

            #exiting the game (update in the future)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            #update
            self.all_sprites.update(dt) #updating all sprites

            #draw
            self.display.fill("Black")
            self.all_sprites.draw(self.display) #drawing all sprites

            #update method to update the screen
            pygame.display.update()
        
        #finishing the game
        pygame.quit()