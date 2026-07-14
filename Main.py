import pygame
import Constantes as con
from Characters.Lilie import Lilie

pygame.init()

screen = pygame.display.set_mode((con.WIDTH, con.HEIGHT))
pygame.display.set_caption("Ender Lilies: Quietus of the Knights - Poor Edition")
clock = pygame.time.Clock()

lilie = Lilie(con.WIDTH // 2, con.HEIGHT // 2 + 50, 100, 180)

running = True

while running:
    dt = clock.tick(con.CLOCK_FPS)

    for event in pygame.event.get():
        #print(event)
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                lilie.moving["left"] = True
            if event.key == pygame.K_d:
                lilie.moving["right"] = True
            if event.key == pygame.K_SPACE:
                lilie.moving["jump"] = True
            if event.key == pygame.K_LSHIFT:
                    lilie.moving["dash"] = True

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                lilie.moving["left"] = False
            if event.key == pygame.K_d:
                lilie.moving["right"] = False

    lilie.update(dt)

    screen.fill((0, 0, 0))
    lilie.draw(screen)
    pygame.display.update()

pygame.quit()
