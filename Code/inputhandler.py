from settings import *

#abstraction layer of input
class InputHandler:
    def __init__(self, up_key, down_key):
        self.actions = {
            "move_up": [up_key],
            "move_down": [down_key]
            #add more later
        }

        #testing
        self.up_key = up_key
        self.down_key = down_key

    def get_action(self, action_name):
        keys = pygame.key.get_pressed()
        for key in self.actions[action_name]:
            if keys[key]:
                return True
        return False
    
    def get_direction(self):
        #using this for singleplayer
        keys = pygame.key.get_pressed()
        return (keys[self.down_key] or 0) - (keys[self.up_key] or 0)

        #old direction
        """
        if player_id == 1:
            if player_team == "TEAM_1":
                return int(keys[pygame.K_s]) - int(keys[pygame.K_w])
            else:
                return int(keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
        """