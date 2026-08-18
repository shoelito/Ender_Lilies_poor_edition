import pygame
import Constantes as con

def handle_inputs(output=None, in_pause = False):
    if in_pause:
        pauseOutputs = ["select", "back"]
        
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
                action = "jump" if not in_pause else "select"
            elif event.key == pygame.K_BACKSPACE:
                action = "back"
            elif event.key == pygame.K_ESCAPE:
                action = "pause" if not in_pause else "back"
            elif event.key == pygame.K_TAB:
                action = "dashboard"
            elif event.key == pygame.K_LSHIFT:
                action = "dash"
            elif event.key == pygame.K_e:
                action = "pray"
            elif event.key == pygame.K_i:
                action = "attack1"
            elif event.key == pygame.K_o:
                action = "attack2"
            elif event.key == pygame.K_p:
                action = "attack3"
            elif event.key == pygame.K_q:
                action = "changeSlot"
                
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
                action = "jump" if not in_pause else "select"
            elif event.button == 1:
                action = "attack3" if not in_pause else "back"
            elif event.button == 4:
                action = "pause" if not in_pause else "back"
            elif event.button == 6:
                action = "dashboard"
            elif event.button == 9:
                action = "dash"
            elif event.button == 10:
                action = "pray"
            elif event.button == 2:
                action = "attack1"
            elif event.button == 3:
                action = "attack2"
            elif event.button == 8:
                action = "changeSlot"
                
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
        if event.type == pygame.JOYBUTTONDOWN:
            print(f"Botón presionado: {event.button}")
            
        if event.type == pygame.JOYAXISMOTION:
            if abs(event.value) > con.AXIS_DEADZONE:
                print(f"Joystick Axis {event.axis} : {event.value:6.3f}")

        if event.type == pygame.JOYHATMOTION:
            print(f"Hat {event.hat} : {event.value}")
    
    return output