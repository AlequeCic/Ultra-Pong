import pygame
from os.path import join


WINDOW_WIDTH, WINDOW_HEIGHT = 1280,720
FPS = 60

OBJECTS_SIZE = {'paddle': (25,75), 'ball': (30,30)  } #size of the game objects

OBJECTS_POSITION = {'TEAM_1': (50, WINDOW_HEIGHT/2), 
                    'TEAM_2': (WINDOW_WIDTH - 60, WINDOW_HEIGHT/2) , 
                    'ball': (WINDOW_WIDTH/2, WINDOW_HEIGHT/2)}

OBJECTS_COLORS = {'TEAM_1':'red', 
                  'TEAM_2': 'cyan', 
                  'ball': 'white'}

OBJECTS_SPEED = {'player': 500, 'ball': 400}