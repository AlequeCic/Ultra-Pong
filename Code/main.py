import pygame
pygame.init()

running = True
dt = 0
WINDOW_WIDTH, WINDOW_HEIGHT = 1280,720
FPS = 60

screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
clock = pygame.time.Clock()
pygame.display.set_caption("Ultra Pong")

#jogador
player_sprite = pygame.Rect(20, screen.get_height()/2 - 120/2,40,  120)

#bola
circle_pos = pygame.Vector2(screen.get_width()/2, screen.get_height()/2)
circle_speed = pygame.Vector2(400,400)
circle_r = 20

while running:
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill("Black")
    #desenhos
    #pygame.draw.circle(screen,"red",player_pos,40)
    pygame.draw.rect(screen,"red", player_sprite)
    pygame.draw.circle(screen, "white",circle_pos, circle_r)

    keys = pygame.key.get_pressed()

    #jogador
    if keys[pygame.K_w] and player_sprite.y > 0:
        player_sprite.y -= 300*dt
    if keys[pygame.K_s] and player_sprite.y + 120 < WINDOW_HEIGHT:
        player_sprite.y += 300 * dt
    #if keys[pygame.K_a]:
        #player_pos.x -= 300 * dt
    #if keys[pygame.K_d]:
       #player_pos.x += 300 * dt

    #bola
    circle_pos.x+= circle_speed.x*dt
    circle_pos.y+= circle_speed.y*dt
    if circle_pos.x - circle_r < 0 or circle_pos.x + circle_r > WINDOW_WIDTH:
        circle_speed.x*= -1
    if circle_pos.y - circle_r < 0 or circle_pos.y + circle_r > WINDOW_HEIGHT:
        circle_speed.y*= -1

    pygame.display.flip()

    dt = clock.tick(FPS) / 1000

pygame.quit()