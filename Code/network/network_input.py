class NetworkInputHandler:
    def __init__(self, network_handler):
        self.network = network_handler
        self._direction = 0.0
    
    def get_direction(self) -> float:
        return self.network.get_opponent_direction()
    
    def set_direction(self, direction: float):
        self._direction = direction
