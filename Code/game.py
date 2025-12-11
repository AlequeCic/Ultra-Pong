import pygame
from settings import *
from player import *  
from gamestate import *
from playingstate import *
from audio_manager import init_audio, get_audio_manager
from playingstate import PlayingState
from menustate import MainMenuState
from menu_state.optionsstate import OptionsState
from menu_state.multiplayerstate import MultiplayerModeState, MultiplayerHostJoinState
from menu_state.waitingstate import WaitingForPlayersState
from menu_state.joinstate import JoinState


# abstraction layer of the game loop
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        pygame.display.set_caption("Ultra Pong")
        
        # Initialize audio system
        init_audio()
        get_audio_manager().play_main_theme(fade_ms=1000)

        # state manager
        self.state_manager = StateManager(self.screen) 

        # registering all states
        self.state_manager.register_state(StateID.MAIN_MENU, MainMenuState)
        self.state_manager.register_state(StateID.OPTIONS, OptionsState)
        self.state_manager.register_state(StateID.PLAYING, PlayingState)
        self.state_manager.register_state(StateID.MULTI_MODE, MultiplayerModeState)
        self.state_manager.register_state(StateID.MULTI_HOST_JOIN, MultiplayerHostJoinState)
        self.state_manager.register_state(StateID.WAITING, WaitingForPlayersState)
        self.state_manager.register_state(StateID.JOIN, JoinState)

        # starter state
        self.state_manager.change_state(StateID.MAIN_MENU)
    
    def run(self):
        while self.state_manager.running:
            #defining fps
            dt = self.clock.tick(FPS) / 1000

            events = pygame.event.get()

            #exiting the game (update in the future)
            for event in events:
                if event.type == pygame.QUIT:
                    self.state_manager.quit()

            self.state_manager.handle_events(events)
            self.state_manager.update(dt)
            self.state_manager.draw()


            #update method to update the screen
            pygame.display.update()
        
        #finishing the game
        get_audio_manager().cleanup()
        pygame.quit()