from settings import FPS

class World:
    def __init__(self):
        self.score = {"TEAM_1": 0, "TEAM_2":0}
        self.phase = "play" # "play", "countdown", "pause_countdown"
        self.tick = 0
        self.countdownEndTick = None
        self.pause_countdownEndTick = None
    
    def start_countdown(self, duration, tick_rate):
        self.phase = "countdown"
        self.countdownEndTick = self.tick + int(duration * tick_rate)

    def start_pause_countdown(self, duration, tick_rate):
        """Inicia countdown para despausar"""
        self.phase = "pause_countdown"
        self.pause_countdownEndTick = self.tick + int(duration * tick_rate)
    
    def maybe_resume(self):
        if self.phase == "countdown" and self.tick >= self.countdownEndTick:
            self.phase = "play"
            self.countdownEndTick = None
            return True

        # Defensive: ensure pause countdown end tick exists (e.g., if phase synced from network)
        if self.phase == "pause_countdown" and self.pause_countdownEndTick is None:
            self.pause_countdownEndTick = self.tick + int(3 * FPS)

        if self.phase == "pause_countdown" and self.tick >= self.pause_countdownEndTick:
            self.phase = "play"
            self.pause_countdownEndTick = None
            return True
        
        return False