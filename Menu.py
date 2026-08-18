import pygame
import os
import sys
import Constantes as con

class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.reloj = pygame.time.Clock()
        
        # Control de estados del menú ("principal" o "seleccion")
        self.estado_actual = "principal"
        
        # Opciones y fuentes del menú principal
        self.opciones_menu = ["Empezar", "Ajustes", "Salir"]
        self.opcion_seleccionada = 0
        self.fuente_menu = pygame.font.Font(None, 40)
        
        # Inicializar atributos de recursos
        self.fondo_Menu = None
        self.sonido_click = None      
        self.sonido_hover = None      
        self.canal_hover = None       
        self.ultimo_hover = -1        
        self.frames_lluvia = []
        self.indice_frame_lluvia = 0
        self.velocidad_lluvia = 0.05
        
        # Atributos para la pantalla de Selección de Partidas (exactamente 3 slots)
        self.slot_seleccionado = 0
        self.img_titulo = None
        self.img_slot = None
        self.img_footer = None
        
        # Cargar todos los recursos al instanciar la clase
        self._cargar_recursos()

    def _cargar_recursos(self):
        # 1. Carga del fondo del menú principal
        try:
            self.fondo_Menu = pygame.image.load("Assets/Menu/Fondo menu.jpg")
            self.fondo_Menu = pygame.transform.scale(self.fondo_Menu, (con.WIDTH, con.HEIGHT))
        except Exception as e:
            print(f"⚠️ Error cargando fondo: {e}")

        # 2. Carga y reproducción de música de fondo
        try:
            archivos_menu = os.listdir("Assets/Menu")
            archivo_audio = next((f for f in archivos_menu if f.endswith(('.mp3', '.wav', '.ogg', '.webm', '.m4a')) and "Sonido" not in f), None)
            if archivo_audio:
                ruta_audio = os.path.join("Assets/Menu", archivo_audio)
                pygame.mixer.music.load(ruta_audio)
                pygame.mixer.music.set_volume(0.5)
                pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"⚠️ Error al reproducir el audio: {e}")

        # 3. Carga del efecto de sonido para Enter / Clic final
        try:
            ruta_sonido = "Assets/Menu/Sonido_Menu_Opciones.mp3"
            if os.path.exists(ruta_sonido):
                self.sonido_click = pygame.mixer.Sound(ruta_sonido)
                self.sonido_click.set_volume(0.8)
        except Exception as e:
            print(f"⚠️ Error al cargar el sonido de clic: {e}")

        # 4. Carga del efecto de sonido corto para el Hover
        try:
            ruta_hover = "Assets/Menu/Sonido_Hover.wav"
            if os.path.exists(ruta_hover):
                self.sonido_hover = pygame.mixer.Sound(ruta_hover)
                self.sonido_hover.set_volume(0.8)
                self.canal_hover = pygame.mixer.Channel(7)
        except Exception as e:
            print(f"⚠️ Error al cargar el sonido de hover: {e}")

        # 5. Carga de los fotogramas de la lluvia animada
        ruta_lluvia = "Assets/Menu/Lluvia"
        try:
            archivos_lluvia = sorted([f for f in os.listdir(ruta_lluvia) if f.endswith('.png')])
            for archivo in archivos_lluvia:
                ruta_completa = os.path.join(ruta_lluvia, archivo)
                img = pygame.image.load(ruta_completa).convert_alpha()
                img = pygame.transform.scale(img, (con.WIDTH, con.HEIGHT))
                img.set_colorkey((0, 0, 0))
                img.set_alpha(35)
                self.frames_lluvia.append(img)
        except Exception as e:
            print(f"⚠️ Error cargando lluvia: {e}")

        # 6. Carga de recursos para la pantalla de Selección de Partida
        base_path_seleccion = "Assets/Menu/Menu_Seleccion_Empezar/"
        try:
            self.img_titulo = pygame.image.load(base_path_seleccion + "Seleccionar_Partida.png").convert_alpha()
            self.img_slot = pygame.image.load(base_path_seleccion + "Menu_Seleccion_Empezar_Nueva_Partida.png").convert_alpha()
            
            img_footer_original = pygame.image.load(base_path_seleccion + "Opciones_Volver_borrar_Partidas_Confirmar.png").convert_alpha()
            nuevo_ancho = int(img_footer_original.get_width() * 0.55)
            nuevo_alto = int(img_footer_original.get_height() * 0.55)
            self.img_footer = pygame.transform.smoothscale(img_footer_original, (nuevo_ancho, nuevo_alto))
        except pygame.error as e:
            print(f"⚠️ Error al cargar imágenes de selección de partida: {e}")

    def ejecutar(self):
        """Bucle principal que gestiona la navegación entre pantallas."""
        while True:
            self.reloj.tick(con.CLOCK_FPS)
            
            if self.estado_actual == "principal":
                self._dibujar_menu_principal()
                accion = self._manejar_menu_principal()
                if accion == "empezar":
                    self.estado_actual = "seleccion"
                elif accion == "salir":
                    pygame.quit()
                    sys.exit()
                
            elif self.estado_actual == "seleccion":
                self._dibujar_seleccion_partida()
                accion = self._manejar_seleccion_partida()
                if accion == "volver":
                    self.estado_actual = "principal"
                elif isinstance(accion, int):
                    return accion  # Retorna el slot elegido para iniciar el juego

            pygame.display.flip()

    def _manejar_menu_principal(self):
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "salir"
            
            elif event.type == pygame.KEYDOWN:
                opcion_anterior = self.opcion_seleccionada
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.opcion_seleccionada = (self.opcion_seleccionada - 1) % len(self.opciones_menu)
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.opcion_seleccionada = (self.opcion_seleccionada + 1) % len(self.opciones_menu)
                
                if self.opcion_seleccionada != opcion_anterior:
                    if self.sonido_hover and self.canal_hover:
                        self.canal_hover.play(self.sonido_hover)
                    self.ultimo_hover = self.opcion_seleccionada

                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    if self.opcion_seleccionada == 0:  # "Empezar"
                        if self.sonido_click:
                            self.sonido_click.play()
                            inicio_espera = pygame.time.get_ticks()
                            while pygame.mixer.get_busy() and pygame.time.get_ticks() - inicio_espera < 150:
                                pygame.time.wait(10)
                        return "empezar"
                    elif self.opcion_seleccionada == 2:  # "Salir"
                        return "salir"

            # --- MANDO: Botones ---
            elif event.type == pygame.JOYBUTTONDOWN:
                opcion_anterior = self.opcion_seleccionada
                if event.button == 11:  # D-pad Arriba
                    self.opcion_seleccionada = (self.opcion_seleccionada - 1) % len(self.opciones_menu)
                elif event.button == 12:  # D-pad Abajo
                    self.opcion_seleccionada = (self.opcion_seleccionada + 1) % len(self.opciones_menu)
                elif event.button == 0:  # X / Cruz → Confirmar
                    if self.opcion_seleccionada == 0:
                        if self.sonido_click:
                            self.sonido_click.play()
                            inicio_espera = pygame.time.get_ticks()
                            while pygame.mixer.get_busy() and pygame.time.get_ticks() - inicio_espera < 150:
                                pygame.time.wait(10)
                        return "empezar"
                    elif self.opcion_seleccionada == 2:
                        return "salir"
                
                if self.opcion_seleccionada != opcion_anterior:
                    if self.sonido_hover and self.canal_hover:
                        self.canal_hover.play(self.sonido_hover)
                    self.ultimo_hover = self.opcion_seleccionada

            # --- MANDO: Joystick izquierdo (eje Y) ---
            elif event.type == pygame.JOYAXISMOTION and event.axis == 1:
                opcion_anterior = self.opcion_seleccionada
                if event.value < -0.5:
                    self.opcion_seleccionada = (self.opcion_seleccionada - 1) % len(self.opciones_menu)
                elif event.value > 0.5:
                    self.opcion_seleccionada = (self.opcion_seleccionada + 1) % len(self.opciones_menu)
                if self.opcion_seleccionada != opcion_anterior:
                    if self.sonido_hover and self.canal_hover:
                        self.canal_hover.play(self.sonido_hover)
                    self.ultimo_hover = self.opcion_seleccionada

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pos_y_base = con.HEIGHT // 2 + 100
                    for i in range(len(self.opciones_menu)):
                        texto_temp = self.fuente_menu.render(self.opciones_menu[i], True, (255, 255, 255))
                        rect_texto = texto_temp.get_rect(center=(con.WIDTH // 2, pos_y_base + (i * 50)))
                        rect_marco = rect_texto.inflate(40, 15)
                        
                        if rect_marco.collidepoint(event.pos):
                            self.opcion_seleccionada = i
                            if self.opcion_seleccionada == 0:  # "Empezar"
                                if self.sonido_click:
                                    self.sonido_click.play()
                                    inicio_espera = pygame.time.get_ticks()
                                    while pygame.mixer.get_busy() and pygame.time.get_ticks() - inicio_espera < 150:
                                        pygame.time.wait(10)
                                return "empezar"
                            elif self.opcion_seleccionada == 2:  # "Salir"
                                return "salir"
        return None

    def _dibujar_menu_principal(self):
        mouse_pos = pygame.mouse.get_pos()
        
        if self.fondo_Menu:
            self.screen.blit(self.fondo_Menu, (0, 0))
        else:
            self.screen.fill((0, 0, 0))

        # Animación de lluvia
        if self.frames_lluvia:
            self.indice_frame_lluvia += self.velocidad_lluvia
            if self.indice_frame_lluvia >= len(self.frames_lluvia):
                self.indice_frame_lluvia = 0
            self.screen.blit(self.frames_lluvia[int(self.indice_frame_lluvia)], (0, 0))

        pos_y_base = con.HEIGHT // 2 + 100
        mouse_sobre_alguno = False

        for i in range(len(self.opciones_menu)):
            texto = self.fuente_menu.render(self.opciones_menu[i], True, (255, 255, 255))
            rect_texto = texto.get_rect(center=(con.WIDTH // 2, pos_y_base + (i * 50)))
            rect_marco = rect_texto.inflate(40, 15)

            if rect_marco.collidepoint(mouse_pos):
                mouse_sobre_alguno = True
                if self.opcion_seleccionada != i:
                    self.opcion_seleccionada = i
                
                if self.ultimo_hover != i:
                    if self.sonido_hover and self.canal_hover:
                        self.canal_hover.play(self.sonido_hover)
                    self.ultimo_hover = i

            if i == self.opcion_seleccionada:
                color = (255, 255, 255)
                texto = self.fuente_menu.render(self.opciones_menu[i], True, color)
                pygame.draw.rect(self.screen, (255, 255, 255), rect_marco, width=2, border_radius=5)
            else:
                color = (150, 150, 150)
                texto = self.fuente_menu.render(self.opciones_menu[i], True, color)

            self.screen.blit(texto, rect_texto)

        if not mouse_sobre_alguno:
            self.ultimo_hover = -1

    def _manejar_seleccion_partida(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.slot_seleccionado = (self.slot_seleccionado - 1) % 3
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.slot_seleccionado = (self.slot_seleccionado + 1) % 3
                elif event.key == pygame.K_RETURN:
                    return self.slot_seleccionado
                # Se agregó pygame.K_b para volver al presionar la letra B
                elif event.key == pygame.K_b or event.key == pygame.K_ESCAPE or event.key == pygame.K_x:
                    return "volver"

            # --- MANDO: Botones ---
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 11:  # D-pad Arriba
                    self.slot_seleccionado = (self.slot_seleccionado - 1) % 3
                elif event.button == 12:  # D-pad Abajo
                    self.slot_seleccionado = (self.slot_seleccionado + 1) % 3
                elif event.button == 0:  # X / Cruz → Confirmar
                    return self.slot_seleccionado
                elif event.button == 1:  # O / Círculo → Volver
                    return "volver"

            # --- MANDO: Joystick izquierdo (eje Y) ---
            elif event.type == pygame.JOYAXISMOTION and event.axis == 1:
                if event.value < -0.5:
                    self.slot_seleccionado = (self.slot_seleccionado - 1) % 3
                elif event.value > 0.5:
                    self.slot_seleccionado = (self.slot_seleccionado + 1) % 3

        return None

    def _dibujar_seleccion_partida(self):
        self.screen.fill((10, 10, 12))

        # 1. Título arriba
        if self.img_titulo:
            titulo_x = con.WIDTH // 2 - self.img_titulo.get_width() // 2
            self.screen.blit(self.img_titulo, (titulo_x, 35))

        # 2. Configuración exacta para las 3 ranuras independientes
        start_y = 150  
        espacio_entre_slots = 120  
        
        if self.img_slot:
            ancho_slot = self.img_slot.get_width()
            alto_slot_individual = self.img_slot.get_height() // 2

            for i in range(3):  # Exactamente 3 slots individuales
                y_pos = start_y + (i * espacio_entre_slots)
                slot_x = con.WIDTH // 2 - ancho_slot // 2
                
                rect_origen = pygame.Rect(0, 0, ancho_slot, alto_slot_individual)
                self.screen.blit(self.img_slot, (slot_x, y_pos), rect_origen)
                
                # Borde blanco exacto y exclusivo para la ranura seleccionada
                if i == self.slot_seleccionado:
                    rect_borde = pygame.Rect(slot_x, y_pos, ancho_slot, alto_slot_individual)
                    pygame.draw.rect(self.screen, (220, 220, 220), rect_borde, 2, border_radius=4)

        # 3. Footer abajo a la derecha
        if self.img_footer:
            footer_x = con.WIDTH - self.img_footer.get_width() - 30  
            footer_y = con.HEIGHT - self.img_footer.get_height() - 25  
            self.screen.blit(self.img_footer, (footer_x, footer_y))