from settings import *

class InputHandler:
    def __init__(self):
        self.actions = {
            "move_up": [pygame.K_w, pygame.K_UP],
            "move_down": [pygame.K_s, pygame.K_DOWN]
            #add more later
        }

    def get_action(self, action_name):
        keys = pygame.key.get_pressed()
        for key in self.actions[action_name]:
            if keys[key]:
                return True
        return False
    
    def get_direction(self, player_id):
        #using this for singleplayer
        keys = pygame.key.get_pressed()
        if player_id == "TEAM_1":
            return int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        else:
            return int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])