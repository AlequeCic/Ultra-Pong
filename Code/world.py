from settings import *

class World:
    def __init__(self):
        self.score = {"TEAM_1": 0, "TEAM_2":0}
        self.phase = "play"
        self.tick = 0
        self.countdownEndTick = None
    
    def start_countdown(self, duration, tick_rate):
        self.phase = "countdown"
        self.countdownEndTick = self.tick + int(duration * tick_rate)
    
    def maybe_resume(self):
        if self.phase == "countdown" and self.tick >= self.countdownEndTick:
            self.phase = "play"
            self.countdownEndTick = None
            return True
        
        return False