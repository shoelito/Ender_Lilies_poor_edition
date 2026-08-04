import pygame
import sys
import Constantes as con
from Menu import Menu
from Characters.Lilie.Lilie import Lilie
from movements import handle_inputs  # Asegúrate de que este sea el nombre exacto del archivo de inputs de tu compañero

def main():
    # Inicialización del motor y canales de audio
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.mixer.set_num_channels(32)

    screen = pygame.display.set_mode((con.WIDTH, con.HEIGHT))
    pygame.display.set_caption("Ender Lilies: Quietus of the Knights - Poor Edition")
    reloj = pygame.time.Clock()

    # 1. Ejecutamos el Menú Principal
    menu_principal = Menu(screen)
    menu_principal.ejecutar()  # Pausa aquí hasta que elijas "Empezar"
    
    lili = Lilie(100, 400, 50, 80)

    # 3. BUCLE PRINCIPAL DEL JUEGO
    acciones_activas = []

    while True:
        dt = reloj.tick(con.CLOCK_FPS)

        # Procesamos los eventos y obtenemos la lista de acciones mediante la función de inputs
        acciones_activas = handle_inputs(acciones_activas)

        # Si el usuario cerró la ventana
        if "quit" in acciones_activas:
            pygame.quit()
            sys.exit()

        # Sincronizamos todas las acciones (movimiento, salto y dash) con el diccionario interno de Lili
        lili.movements(acciones_activas)
        lili.update(dt)

        # Renderizado / Dibujo en pantalla
        screen.fill((20, 20, 30))  # Fondo del nivel
        
        # Dibujamos a Lili en pantalla
        if hasattr(lili, 'draw'):
            lili.draw(screen)

        pygame.display.flip()

if __name__ == "__main__":
    main()