import pygame
from os.path import join
from random import choice, uniform
from collections import deque
from math import pi, cos,sin
from enum import Enum, auto

WINDOW_WIDTH, WINDOW_HEIGHT = 1280,720
FPS = 60

OBJECTS_SIZE = {'paddle': (25,75), 'ball': (30,30)  } #size of the game objects

OBJECTS_POSITION = {'TEAM_1': (50, WINDOW_HEIGHT/2), 
                    'TEAM_2': (WINDOW_WIDTH - 60, WINDOW_HEIGHT/2) , 
                    'ball': (WINDOW_WIDTH/2, WINDOW_HEIGHT/2)}

OBJECTS_COLORS = {'TEAM_1':'#d13f3f', 
                  'TEAM_2': 'cyan', 
                  'ball': 'white'}

OBJECTS_SPEED = {'player': 500, 'ball': 400}

COUNTDOWN = {'ball': 3.0}

class GameState(Enum):
    MENU = auto()
    LOCAL_COOP = auto()
    PAUSED = auto()

