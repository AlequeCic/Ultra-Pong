from settings import *

class StateID:
    MAIN_MENU = "main_menu"
    PLAYING = "playing"

#abstraction layer of game states (menu, game, etc)
class BaseState:
    def __init__(self, state_manager):
        self.state_manager = state_manager
        self.screen = state_manager.screen
    
    def enter(self, **kwards):
        pass

    def exit(self):
        pass

    def handle_events(self, events):
        pass

    def update(self, dt):
        pass

    def draw(self):
        pass

class StateManager:
    def __init__(self, screen):
        self.screen = screen
        self.states = {}
        self.current_state = None
        self.running = True

    def register_state(self, state_id, state_class):
        self.states[state_id] = state_class
    
    def change_state(self, new_state_id, **kwargs):
        #changing to a new state
        if self.current_state:
            self.current_state.exit() #exit the old state

        if new_state_id in self.states: #checks if new states exists
            self.current_state = self.states[new_state_id](self)
            self.current_state.enter(**kwargs)
        else:
            raise ValueError({new_state_id})
        
    def handle_events(self, events):
        if self.current_state:
            self.current_state.handle_events(events)

    def update(self, dt):
        if self.current_state:
            self.current_state.update(dt)
            
    def draw(self):
        if self.current_state:
            self.current_state.draw()
            
    def quit(self):
        self.running = False