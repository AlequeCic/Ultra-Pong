from settings import *

# countdown.py
import pygame
from settings import *

class CountdownDisplay:
    def __init__(self, screen, world):
        self.screen = screen
        self.world = world
        
        # Fontes
        self.countdown_font = pygame.font.Font(None, 140)
        self.small_font = pygame.font.Font(None, 24)
        
        # Estado
        self.is_visible = False
        self.current_value = 0
        self.message = ""
        self.color = "white"
    
    def update(self):
        """Atualiza o estado do countdown baseado no mundo do jogo"""
        if not self.world:
            self.is_visible = False
            return
        
        # Countdown de despausa
        if self.world.phase == "pause_countdown":
            if self.world.pause_countdownEndTick is not None:
                remaining_ticks = self.world.pause_countdownEndTick - self.world.tick
                secs_left = remaining_ticks / FPS
                self.current_value = int(secs_left) + 1
                self.message = "Game resuming in"
                self.color = "yellow"
                self.is_visible = True
            else:
                self.is_visible = False
            return
        
        # Countdown normal (após gol)
        if self.world.phase == "countdown":
            remaining_ticks = self.world.countdownEndTick - self.world.tick
            secs_left = remaining_ticks / FPS
            self.current_value = int(secs_left) + 1
            self.message = ""
            self.color = "white"
            self.is_visible = True
            return
        
        self.is_visible = False
    
    def draw(self):
        """Desenha o countdown na tela"""
        if not self.is_visible:
            return
        
        center_x = self.screen.get_width() // 2
        center_y = self.screen.get_height() // 2
        
        # Número principal
        countdown_surf = self.countdown_font.render(str(self.current_value), True, self.color)
        countdown_rect = countdown_surf.get_frect(center=(center_x, center_y - 80))
        self.screen.blit(countdown_surf, countdown_rect)
        
        # Mensagem (se houver)
        if self.message:
            message_surf = self.small_font.render(self.message, True, (200, 200, 100))
            message_rect = message_surf.get_frect(center=(center_x, center_y + 20))
            self.screen.blit(message_surf, message_rect)
    
    def reset(self):
        """Reseta o countdown"""
        self.is_visible = False
        self.current_value = 0
        self.message = ""
        self.color = "white"


class ScoreDisplay:
    def __init__(self, screen, world):
        self.screen = screen
        self.world = world
        
        # Fonte para placar
        self.score_font = pygame.font.Font(None, 80)
    
    def update_score(self, side):
        """Atualiza o placar e reinicia o countdown"""
        self.world.score[side] += 1
        self.world.start_countdown(3.0, FPS)  # 3 seconds
        
        if self.world.ball is not None:
            # put the ball in the middle and randomize its direction
            self.world.ball.reset()
    
    def draw(self):
        """Desenha o placar na tela"""
        if not self.world:
            return
        
        # team_1
        team_1_surf = self.score_font.render(
            str(self.world.score['TEAM_1']), True, OBJECTS_COLORS['TEAM_1']
        )
        team_1_rect = team_1_surf.get_frect(
            center=(WINDOW_WIDTH/2 - WINDOW_WIDTH/4, 40)
        )
        self.screen.blit(team_1_surf, team_1_rect)

        # team_2
        team_2_surf = self.score_font.render(
            str(self.world.score['TEAM_2']), True, OBJECTS_COLORS['TEAM_2']
        )
        team_2_rect = team_2_surf.get_frect(
            center=(WINDOW_WIDTH/2 + WINDOW_WIDTH/4, 40)
        )
        self.screen.blit(team_2_surf, team_2_rect)