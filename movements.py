import pygame
import Constantes as con

def handle_inputs(output=None):
    for event in pygame.event.get():
        if output is None:
            output = []

        # Evento de Salida
        if event.type == pygame.QUIT:
            if "quit" not in output:
                output.append("quit")
            return output

        action = None

        # TECLADO 
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            if event.key == pygame.K_a:
                action = "left"
            elif event.key == pygame.K_d:
                action = "right"
            elif event.key == pygame.K_w:
                action = "up"
            elif event.key == pygame.K_s:
                action = "down"
            elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                action = "select"
            elif event.key == pygame.K_BACKSPACE:
                action = "back"
            elif event.key == pygame.K_ESCAPE:
                action = "pause"

        # BOTONES DEL MANDO 
        elif event.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP):
            if event.button == 13:
                action = "left"
            elif event.button == 14:
                action = "right"
            elif event.button == 11:
                action = "up"
            elif event.button == 12:
                action = "down"
            elif event.button == 0:
                action = "select"
            elif event.button == 1:
                action = "back"
            elif event.button == 6:
                action = "pause"
            
            

        # JOYSTICK
        elif event.type == pygame.JOYAXISMOTION:
            if event.axis == 0:
                if event.value < -con.AXIS_DEADZONE:
                    if "left" not in output:
                        output.append("left")
                    if "right" in output:
                        output.remove("right")

                elif event.value > con.AXIS_DEADZONE:
                    if "right" not in output:
                        output.append("right")
                    if "left" in output:
                        output.remove("left")

                else:
                    if "left" in output:
                        output.remove("left")
                    if "right" in output:
                        output.remove("right")
            if event.axis == 1:
                if event.value < -con.AXIS_DEADZONE:
                    if "up" not in output:
                        output.append("up")
                    if "down" in output:
                        output.remove("down")
                elif event.value > con.AXIS_DEADZONE:
                    if "down" not in output:
                        output.append("down")
                    if "up" in output:
                        output.remove("up")
                else:
                    if "up" in output:
                        output.remove("up")
                    if "down" in output:
                        output.remove("down")

        # Procesar Presionar
        is_down_event = (
            event.type in (pygame.KEYDOWN, pygame.JOYBUTTONDOWN) 
        )
        if is_down_event and action:
            if action not in output:
                output.append(action)

        # Procesar Soltar
        is_up_event = (
            event.type in (pygame.KEYUP, pygame.JOYBUTTONUP) 
        )
        if is_up_event and action and action in output:
            output.remove(action)

        # DEBUGS 
        '''if event.type == pygame.JOYBUTTONDOWN:
            print(f"Botón presionado: {event.button}")
            
        if event.type == pygame.JOYAXISMOTION and event.axis == 0:
            if abs(event.value) > con.AXIS_DEADZONE:
                print(f"Joystick Axis {event.axis} : {event.value:6.3f}")'''
        
    return output