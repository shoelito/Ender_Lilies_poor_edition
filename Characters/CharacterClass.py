import pygame
import os
import Constantes as con

class Character:
    #Inicializa el personaje
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.speed = con.SPEED
        self.hitbox = pygame.Rect(self.x, self.y, self.width, self.height)
        self.show_hitbox = con.SHOW_HITBOX

    #Mueve el personaje
    def move(self, direction):
        if direction == "right":
            self.x += self.speed
        elif direction == "left":
            self.x -= self.speed
        elif direction == "up":
            self.y -= self.speed
        elif direction == "down":
            self.y += self.speed
        self.hitbox.x = self.x
        self.hitbox.y = self.y
    
    #Dibuja el personaje en la pantalla
    def draw(self, screen, frame):
        screen.blit(frame, (self.x, self.y))
        if self.show_hitbox:
            pygame.draw.rect(screen, (255, 0, 0), self.hitbox, 2)


    #Carga los frames de una animación
    #folder: carpeta donde se encuentran los frames
    #prefix: prefijo del nombre de los frames o nombre de animación
    #count: cantidad de frames
    #extension: extension de los frames
    @staticmethod
    def _load_frames(folder, prefix, count, extension="png"):
        frames = []
        folder = os.path.join(con.ASSETS_PATH, folder)
        path = os.path.join(folder)
        for f in sorted(os.listdir(path)):
            if f.lower().endswith(f".{extension}"):
                img = pygame.image.load(os.path.join(path, f)).convert_alpha()
                frames.append(img)
        return frames

    #Obtiene el frame con su tamaño y dirección
    def _get_scaled_frame(self):
        frames = self.animations[self.state]
        frame = frames[self.frame_index % len(frames)]
        scaled = pygame.transform.scale(frame, (self.width, self.height))
        is_flip = not self.facing_right
        if is_flip:
            scaled = pygame.transform.flip(scaled, True, False)
        return (scaled, is_flip)