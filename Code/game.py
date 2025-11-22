from settings import *
from player import *
from gamestate import *
from playingstate import *

#abstraction layer of th game loop
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("Ultra Pong")

        #state manager
        self.state_manager = StateManager(self.screen) 
        
        #registering all states
        self.state_manager.register_state(StateID.PLAYING, PlayingState)

        #starter state
        self.state_manager.change_state(StateID.PLAYING) #in this case playing the game
    
    def run(self):
        while self.state_manager.running:
            #defining fps
            dt = self.clock.tick(FPS) / 1000

            events = pygame.event.get()

            #exiting the game (update in the future)
            for event in events:
                if event.type == pygame.QUIT:
                    self.state_manager.quit()
            #update
            self.state_manager.handle_events(events)
            self.state_manager.update(dt)
            self.state_manager.draw()


            #update method to update the screen
            pygame.display.update()
        
        #finishing the game
        pygame.quit()