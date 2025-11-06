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
player_score =0

#bola
circle_pos = pygame.Vector2(screen.get_width()/2, screen.get_height()/2)
circle_speed = pygame.Vector2(400,400)
circle_r = 20
circle_surf = pygame.Surface((circle_r*2,circle_r*2), pygame.SRCALPHA)
pygame.draw.circle(circle_surf, "white",(circle_r,circle_r), circle_r)
circle_rect = circle_surf.get_rect(center=circle_pos)

#inimigo
enemy_sprite = pygame.Rect(screen.get_width() - 60, screen.get_height()/2 - 120/2, 40, 120)
enemy_direction = 300
enemy_score = 0

while running:
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill("Black")
    #desenhos
    #pygame.draw.circle(screen,"red",player_pos,40)
    pygame.draw.rect(screen,"red", player_sprite)
    pygame.draw.rect(screen, "blue", enemy_sprite)
    screen.blit(circle_surf,circle_rect)

    keys = pygame.key.get_pressed()

    #jogador
    if keys[pygame.K_w] and player_sprite.top > 0:
        player_sprite.y -= 300*dt
    if keys[pygame.K_s] and player_sprite.bottom < WINDOW_HEIGHT:
        player_sprite.y += 300 * dt
    #if keys[pygame.K_a]:
        #player_pos.x -= 300 * dt
    #if keys[pygame.K_d]:
       #player_pos.x += 300 * dt

    #bola
    circle_rect.x+= circle_speed.x*dt
    circle_rect.y+= circle_speed.y*dt

    if circle_rect.top < 0 or circle_rect.bottom > WINDOW_HEIGHT:
        circle_speed.y*= -1
    if circle_rect.left < 0:
        enemy_score+=1
        circle_rect.centery = screen.get_height()/2
        circle_rect.centerx = screen.get_width()/2
    if circle_rect.right > WINDOW_WIDTH:
        player_score+=1
        circle_rect.centery = screen.get_height()/2
        circle_rect.centerx = screen.get_width()/2

    #inimigo
    if (enemy_sprite.centery < circle_rect.centery) and (enemy_sprite.top > 0):
        enemy_sprite.y += enemy_direction*dt
        if enemy_sprite.top < 0:
            enemy_sprite.top = 1
    if (enemy_sprite.centery > circle_rect.centery) and (enemy_sprite.bottom < WINDOW_HEIGHT):
        enemy_sprite.y -= enemy_direction*dt
        if enemy_sprite.bottom > WINDOW_HEIGHT:
            enemy_sprite.bottom = WINDOW_HEIGHT -1

    #colisao
    if circle_rect.colliderect(player_sprite) and circle_speed.x < 0: #player
        circle_speed.x*=-1
        circle_rect.left = player_sprite.right + 2
    if circle_rect.colliderect(enemy_sprite) and circle_speed.x > 0: #inimigo
        circle_speed.x*=-1
        circle_rect.right = enemy_sprite.left - 2

    pygame.display.flip()

    print(f"Jogardor: {player_score}\n")
    print(f"Inimigo: {enemy_score}\n")


    dt = clock.tick(FPS) / 1000

pygame.quit()