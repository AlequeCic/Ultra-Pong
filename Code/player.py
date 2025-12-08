from settings import *
from inputhandler import *
from audio_manager import get_audio_manager

#abstraction layer of the paddles
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
                    get_audio_manager().play_paddle_hit()
                elif self.rect.bottom > WINDOW_HEIGHT:
                    self.rect.bottom = WINDOW_HEIGHT
                    self.vel = -self.vel*2/3
                    get_audio_manager().play_paddle_hit()
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
        #print(self.vel)
    
#abstraction layer 
class Player(Paddle):
    
    def __init__(self, team, input_handler, groups):
        super().__init__(team,groups)
        self.team = team
        self.id = id
        #movement
        self.max_speed = OBJECTS_SPEED['player']
        self.input_handler = input_handler
        
        #launch
        self.max_launch_speed = self.max_speed*2.0
     
    def get_direction(self):
        self.direction = self.input_handler.get_direction()

#abstraction layer of the ball
class Ball(pygame.sprite.Sprite):
    def __init__(self, groups, paddle_sprites, update_score):
        super().__init__(groups)
        self.paddle_sprites = paddle_sprites
        self.update_score  = update_score

         #image of the ball
        self.image = pygame.Surface(OBJECTS_SIZE['ball'], pygame.SRCALPHA)
        pygame.draw.circle(self.image, OBJECTS_COLORS['ball'], (OBJECTS_SIZE['ball'][0]/2,OBJECTS_SIZE['ball'][1]/2 ), OBJECTS_SIZE['ball'][0]/2)

         #rectangle (for collision)
        self.rect = self.image.get_frect(center = OBJECTS_POSITION['ball'])
        self.old_rect = self.rect.copy()
         #movement
        self.direction = pygame.Vector2(choice((1,-1)),uniform(0.7,0.8) * choice((-1,1)))
        self.speed = OBJECTS_SPEED['ball']
        #self.is_frozen = False

        #trail
        self.trail = deque(maxlen = 6)
        self.trail_life = 0.4
        self.trail_spacing = 0.08
        self.last_trail_time = 0
        self.trail_surfaces = None
           
    def move(self, dt):

        self.rect.x += self.direction.x * self.speed * dt
        self.paddle_collission('horizontal')
        self.rect.y += self.direction.y * self.speed * dt
        self.paddle_collission('vertical')

    def wall_collision(self):
        #top window collision
        if self.rect.top < 0:
            self.rect.top = 0
            self.direction.y *=-1
            # pan based on ball horizontal position (-0.7 left to 0.7 right)
            pan = -0.7 + (self.rect.centerx / WINDOW_WIDTH) * 1.4
            get_audio_manager().play_wall_hit(pan=pan)
        
        #bottom windows collision
        if self.rect.bottom > WINDOW_HEIGHT:
            self.rect.bottom = WINDOW_HEIGHT
            self.direction.y *= -1
            # pan based on ball horizontal position (-0.7 left to 0.7 right)
            pan = -0.7 + (self.rect.centerx / WINDOW_WIDTH) * 1.4
            get_audio_manager().play_wall_hit(pan=pan)

        #getting score
        if self.rect.left  <= 0 or self.rect.right >= WINDOW_WIDTH:
            self.update_score('TEAM_2' if self.rect.x < WINDOW_WIDTH/2 else 'TEAM_1')
            self.reset()

        '''
        #for developing
        if self.rect.right > WINDOW_WIDTH:
            self.rect.right = WINDOW_WIDTH
            self.direction.x*=-1
        '''

    def paddle_collission(self, direction):
        for sprite in self.paddle_sprites:
            if sprite.rect.colliderect(self.rect):
                if direction == 'horizontal':
                    self._handle_paddle_collision(sprite)

                else:
                    if self.rect.bottom >= sprite.rect.top and self.old_rect.bottom <= sprite.old_rect.top:
                        self.rect.bottom = sprite.rect.top
                        self.direction.y *= -1
                    elif self.rect.top <= sprite.rect.bottom and self.old_rect.top >= sprite.old_rect.bottom:
                        self.rect.top = sprite.rect.bottom
                        self.direction.y*=-1

                ''' here is old collision method
                    if self.rect.right > sprite.rect.left and self.old_rect.right <= sprite.old_rect.left:
                        self.rect.right = sprite.rect.left
                        self.direction.x *=-1
                    elif self.rect.left < sprite.rect.right and self.old_rect.left >= sprite.old_rect.left:
                        self.rect.left = self.rect.right
                        self.direction.x *=-1
                '''
    
    def _handle_paddle_collision(self, paddle):
        relative_intersect_y = (paddle.rect.centery - self.rect.centery)/ paddle.rect.height/2

        #limiting value bet -1 and 1
        relative_intersect_y = max(-1, min(1,relative_intersect_y))

        smooth_intersect = relative_intersect_y * abs(relative_intersect_y)
        #defining angle
        max_bounce_angle = pi/3

        bounce_angle = smooth_intersect * max_bounce_angle

        #finding which team is the paddle from
        if paddle.rect.centerx < WINDOW_WIDTH / 2:
            new_direction_x = 1
            pan = -0.7  # Left paddle: pan to right
        else:
            new_direction_x = -1
            pan = 0.7   # Right paddle: pan to left
        
        #applying angle
        self.direction.x = new_direction_x * cos(bounce_angle)
        self.direction.y = -sin(bounce_angle)
        
        # Play paddle hit sound with velocity and panning
        get_audio_manager().play_ball_paddle_hit(velocity=self.speed, pan=pan)


        #paddle effect in the bounce
        if abs(paddle.vel) > 150:
            paddle_effect = (paddle.vel / paddle.max_launch_speed )* 0.3
            self.direction.y -= paddle_effect

        #normalizing vector
        self.direction = self.direction.normalize()

        #increasing speed after bouncing in the paddle
        self.speed = min(self.speed * 1.1, OBJECTS_SPEED['ball']*2)

        self._prevent_stuck(paddle)

    def _prevent_stuck(self, paddle):

        if self.direction.x > 0 and paddle.rect.centerx < WINDOW_WIDTH / 2:
            self.rect.left = paddle.rect.right + 3
        elif self.direction.x < 0 and paddle.rect.centerx > WINDOW_WIDTH / 2:
            self.rect.right = paddle.rect.left - 3

    def draw_trail(self, surface):
        if not self.trail:
            return
        
        if self.trail_surfaces is None:
            self.trail_surfaces = {}
        length = len(self.trail)
  
        for i, (x, y, life, base_size) in enumerate(reversed(self.trail)):
            progress = i / length  
            life_fraction = max(0.0, life / self.trail_life)
      
            size_scale = life_fraction * (0.8 + 0.6 * (1 - progress))
            current_size = max(2, int(base_size * size_scale))
            trail_surf = self.trail_surfaces.get(current_size)
            if trail_surf is None:
                trail_surf = pygame.Surface((current_size * 2, current_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf, OBJECTS_COLORS['ball'], (current_size, current_size), current_size)
                self.trail_surfaces[current_size] = trail_surf
            alpha = int(255 * life_fraction * (1 - progress))
            if alpha < 5:
                continue
            trail_surf.set_alpha(alpha)
            surface.blit(trail_surf, (int(x) - current_size, int(y) - current_size))


        '''OLD WAY    
        for i, (x, y, life, size) in enumerate(self.trail):
            progress = i / len(self.trail) 
            life_progress = life / self.trail_life 
            
            # time dilation size
            current_size = int(size * (1 - progress * 0.7) * life_progress)
            
            if current_size <= 0:
                continue
                
            # opacity time dilation
            alpha = int(255 * (1 - progress * 0.5) * life_progress)
            
            if alpha <= 0:
                continue
                
            # trail draw
            trail_surf = pygame.Surface((current_size * 2, current_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(trail_surf, (255, 255, 255, alpha), 
                             (current_size, current_size), current_size)
            
            # Desenha no display
            surface.blit(trail_surf, (int(x) - current_size, int(y) - current_size))
        '''
    
    def _update_trail(self, dt):
        
        self.last_trail_time += dt
        if self.last_trail_time >= self.trail_spacing:
            
            base_size = OBJECTS_SIZE['ball'][0] // 2
            self.trail.appendleft([
                self.rect.centerx, 
                self.rect.centery, 
                self.trail_life,
                base_size
            ])
            self.last_trail_time = 0
        
        #update every trail
        for sample in self.trail:
            sample[2] -= dt 
        
        #remove small ones
        while self.trail and self.trail[-1][2] <= 0:
            self.trail.pop()

    def reset(self):
        self.rect.center = OBJECTS_POSITION['ball']
        self.direction = pygame.Vector2(0,0)
        #self.is_frozen = True
        self.speed = OBJECTS_SPEED['ball']

    def launch_after_countdown(self):
        #self.is_frozen = False
        self.direction = pygame.Vector2(choice((1,-1)), uniform(0.7,0.8) * choice((-1,1)))
        self.speed = OBJECTS_SPEED['ball']

    def update(self, dt):
        self.old_rect = self.rect.copy()
        self._update_trail(dt)
        self.move(dt)
        self.wall_collision()
