import pygame


def handle_inputs(event, output = []):
    
    #print(event)
            
    if event.type == pygame.QUIT:
        output.append("quit")

    if event.type == pygame.KEYDOWN or event.type == pygame.JOYBUTTONDOWN or event.type == pygame.JOYHATMOTION:
        if event == pygame.K_a or event.button == 13 or event == (1, 0):
            output.append("left")
        if event == pygame.K_d or event.button == 14 or event == (-1, 0):
            output.append("right")
        if event == pygame.K_SPACE or event.button == 1 or event == (0, 1):
            output.append("jump")
        if event == pygame.K_LSHIFT or event.button == 3 or event == (0, -1):
            output.append("dash")

    if event.type == pygame.KEYUP or event.type == pygame.JOYBUTTONUP or event.type == pygame.JOYHATMOTION:
        if event == pygame.K_a or event.button == 0 or event == (1, 0):
            output.remove("left")
        if event == pygame.K_d or event.button == 2 or event == (-1, 0):
            output.remove("right")
        if event == pygame.K_SPACE or event.button == 1 or event == (0, 1):
            output.remove("jump")
        if event == pygame.K_LSHIFT or event.button == 3 or event == (0, -1):
            output.remove("dash")
            
    if event.type == pygame.JOYBUTTONDOWN:
        print(event.button)
    
    return output