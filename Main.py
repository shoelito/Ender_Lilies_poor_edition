import movements
import pygame
import Constantes as con
from Characters.Lilie import Lilie

pygame.init()
pygame.joystick.init()
joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]

screen = pygame.display.set_mode((con.WIDTH, con.HEIGHT))
pygame.display.set_caption("Ender Lilies: Quietus of the Knights - Poor Edition")
clock = pygame.time.Clock()

lilie = Lilie(con.WIDTH // 3, con.HEIGHT // 3 + 50, 60, 110)
running = True
outputs = []

#Menu flag
in_pause_menu = False
is_pressed = False

while running:
    dt = clock.tick(con.CLOCK_FPS)

    
    outputs = movements.handle_inputs(outputs)
    print(outputs)

    if "pause" in outputs and not is_pressed:
        is_pressed = True
        in_pause_menu = not in_pause_menu

    if "pause" not in outputs:
        is_pressed = False

    for output in outputs:
        if output == "quit":
            running = False
            
    if not in_pause_menu:
        lilie.move(outputs)
        lilie.update(dt)
    else:
        #Menu logic
        pass
    

    screen.fill((0, 20, 0))
    lilie.draw(screen)
    pygame.display.update()

pygame.quit()
