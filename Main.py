import movements
import pygame
import Constantes as con
from Characters.Lilie import Lilie

pygame.init()
pygame.joystick.init()
joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]

print(joysticks)

screen = pygame.display.set_mode((con.WIDTH, con.HEIGHT))
pygame.display.set_caption("Ender Lilies: Quietus of the Knights - Poor Edition")
clock = pygame.time.Clock()

lilie = Lilie(con.WIDTH // 2, con.HEIGHT // 2 + 50, 100, 180)

running = True

outputs = []

while running:
    dt = clock.tick(con.CLOCK_FPS)

    for event in pygame.event.get():
        #print()
        outputs = movements.handle_inputs(event, outputs)

    for output in outputs:
        if output == "quit":
            running = False

    screen.fill((0, 0, 0))
    lilie.draw(screen)
    pygame.display.update()

pygame.quit()
