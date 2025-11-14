from settings import *
from game import *
import socket
import threading
import json
import time

if __name__ == '__main__':
    game = Game()
    game.run()
