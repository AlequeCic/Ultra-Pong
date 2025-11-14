from settings import *
from random import choice, uniform

class Paddle(pygame.sprite.Sprite):
    def __init__(self, team, groups):
        super().__init__(groups)

        #image of the player
        self.image = pygame.Surface(OBJECTS_SIZE['paddle'])
        self.image.fill(OBJECTS_COLORS[team])

        #rectangle (for collision)
        self.rect = self.image.get_frect(center = OBJECTS_POSITION[team])
        self.old_rect = self.rect.copy()
        
        #movement
        self.direction = 0
        self.vel = 0.0
        self.acceleration = 600.0
        self.deceleration = 500.0
        self.k = 2.0

        #charging variables
        self.charge_time = 0.0
        self.charge_max = 1.5
        self.tap_treshold = 0.20
        self.tap_multiplier = 0.5
        self.charge_multiplier = 2.5
        self.is_charging = False
        self.prev_input = 0


    def move(self, dt):
        #updating speed
        '''
        #old_acceleration
        if self.direction != 0:
            self.vel+= self.direction*self.acceleration*dt
            #max speed
            self.vel = self.max_speed if self.vel > self.max_speed else self.vel
            self.vel = -self.max_speed if self.vel < -self.max_speed else self.vel

        '''
        if self.is_charging:
            self.nudge(dt)
        else:
            if self.vel != 0:
                #movement
                self.rect.centery += self.vel * dt
                #making the plyer stay in the screen
                if self.rect.top < 0:
                    self.rect.top = 0
                    self.vel = -self.vel*2/3
                elif self.rect.bottom > WINDOW_HEIGHT:
                    self.rect.bottom = WINDOW_HEIGHT
                    self.vel = -self.vel*2/3
                #friction
                if self.vel > 0:
                    #self.vel-= self.deceleration*dt
                    self.vel *= max(0.0, 1.0 - self.k*dt)
                    #min speed
                elif self.vel < 0:
                    #self.vel += self.deceleration * dt
                    self.vel *= max(0.0, 1.0 -self.k*dt)
                if abs(self.vel) < 10.0:
                    self.vel = 0.0

    def charge(self, dt):
        if self.direction != 0:
            #charging
            self.is_charging = True
            self.charge_time = min(self.charge_max, self.charge_time + dt)
            self.prev_input = self.direction
        
        else:
            if self.is_charging:

                if self.charge_time < self.tap_treshold:
                    launch_speed = self.max_speed * self.tap_multiplier
                
                else:
                    power = self.charge_time / self.charge_max
                    launch_speed = self.max_speed * (1.0 + power * self.charge_multiplier)

                launch_speed = self.max_launch_speed if launch_speed> self.max_launch_speed else launch_speed

                self.vel = launch_speed * (1 if self.prev_input > 0 else - 1)

                #max_vel
                self.vel = self.max_launch_speed if self.vel > self.max_launch_speed else self.vel
                self.vel = -self.max_launch_speed if self.vel < -self.max_launch_speed else self.vel

                #resetting
                self.charge_time = 0.0
                self.is_charging = False
                self.prev_input = 0

    def nudge(self, dt):
        nudge = 10* (self.charge_time / self.charge_max)
        self.rect.centery += self.direction * nudge * dt

    def update(self, dt):
        self.old_rect = self.rect.copy() #copying it before the movement
        self.get_direction()
        self.charge(dt)
        self.move(dt)
        print(self.vel)
    
class Player(Paddle):
    
    def __init__(self, team, groups):
        super().__init__(team,groups)

        #movement
        self.max_speed = OBJECTS_SPEED['player']
        
        #launch
        self.max_launch_speed = self.max_speed*1.5
        

    def get_direction(self):
        keys = pygame.key.get_pressed()
        self.direction = int(keys[pygame.K_s]) - int(keys[pygame.K_w])


class Ball(pygame.sprite.Sprite):
    def __init__(self, groups, paddle_sprites):
        super().__init__(groups)
        self.paddle_sprites = paddle_sprites

         #image of the ball
        self.image = pygame.Surface(OBJECTS_SIZE['ball'], pygame.SRCALPHA)
        pygame.draw.circle(self.image, OBJECTS_COLORS['ball'], (OBJECTS_SIZE['ball'][0]/2,OBJECTS_SIZE['ball'][1]/2 ), OBJECTS_SIZE['ball'][0]/2)

         #rectangle (for collision)
        self.rect = self.image.get_frect(center = OBJECTS_POSITION['ball'])
        self.old_rect = self.rect.copy()
         #movement
        self.direction = pygame.Vector2(choice((1,-1)),uniform(0.7,0.8) * choice((-1,1)))
        
    def move(self, dt):
        self.rect.x += self.direction.x * OBJECTS_SPEED['ball'] * dt
        self.paddle_collission('horizontal')
        self.rect.y += self.direction.y * OBJECTS_SPEED['ball'] * dt
        self.paddle_collission('vertical')

    def wall_collision(self):
        #top window collision
        if self.rect.top < 0:
            self.rect.top = 0
            self.direction.y *=-1
        
        #bottom windows collision
        if self.rect.bottom > WINDOW_HEIGHT:
            self.rect.bottom = WINDOW_HEIGHT
            self.direction.y *= -1

        #for developing
        if self.rect.right > WINDOW_WIDTH:
            self.rect.right = WINDOW_WIDTH
            self.direction.x*=-1
    
    def paddle_collission(self, direction):
        for sprite in self.paddle_sprites:
            if sprite.rect.colliderect(self.rect):
                if direction == 'horizontal':
                    if self.rect.right > sprite.rect.left and self.old_rect.right <= sprite.old_rect.left:
                        self.rect.right = sprite.rect.left
                        self.direction.x *=-1
                    elif self.rect.left < sprite.rect.right and self.old_rect.left >= sprite.old_rect.left:
                        self.rect.left = self.rect.right
                        self.direction.x *=-1
                else:
                    if self.rect.bottom >= sprite.rect.top and self.old_rect.bottom <= sprite.old_rect.top:
                        self.rect.bottom = sprite.rect.top
                        self.direction.y *= -1
                    elif self.rect.top <= sprite.rect.bottom and self.old_rect.top >= sprite.old_rect.bottom:
                        self.rect.top = sprite.rect.bottom
                        self.direction.y*=-1
    
    def update(self, dt):
        self.old_rect = self.rect.copy()
        self.move(dt)
        self.wall_collision()
