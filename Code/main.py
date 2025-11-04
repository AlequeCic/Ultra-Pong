import pygame

pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 1920,1080
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
clock = pygame.time.Clock()
running = True

while running:
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill("Black")

    pygame.display.flip()

    clock.tick(60)

pygame.quit()