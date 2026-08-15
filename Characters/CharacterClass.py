import pygame
import os
import re
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

        # Ordena por el número en el nombre del archivo (jump10 va después de
        # jump9, no antes de jump2 como pasaría con un sort alfabético normal)
        def frame_sort_key(filename):
            match = re.search(r"(\d+)", filename)
            return (int(match.group(1)) if match else float("inf"), filename)

        for f in sorted(os.listdir(path), key=frame_sort_key):
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

    #Rect (en coordenadas del frame sin escalar) que encierra los píxeles
    #no transparentes de un sprite, para armar hitboxes ajustadas al dibujo
    #real en vez de a todo el lienzo width x height.
    @staticmethod
    def _alpha_bounds(surface):
        rects = pygame.mask.from_surface(surface).get_bounding_rects()
        if not rects:
            return pygame.Rect(0, 0, 0, 0)
        bounds = rects[0].copy()
        for r in rects[1:]:
            bounds.union_ip(r)
        return bounds

    #Ajusta self.hitbox a los píxeles visibles del frame actual (según
    #self.state/self.frame_index) en vez de al rectángulo width x height
    #completo. Requiere que la subclase haya armado self.animation_bounds
    #con Character._alpha_bounds() para cada frame de self.animations.
    def _sync_hitbox(self):
        frames = self.animations[self.state]
        index = self.frame_index % len(frames)
        raw = frames[index]
        bounds = self.animation_bounds[self.state][index]

        scale_x = self.width / raw.get_width()
        scale_y = self.height / raw.get_height()

        scaled_w = max(1, round(bounds.width * scale_x))
        scaled_h = max(1, round(bounds.height * scale_y))
        scaled_x = round(bounds.x * scale_x)
        scaled_y = round(bounds.y * scale_y)

        if not self.facing_right:
            scaled_x = self.width - scaled_x - scaled_w

        self.hitbox.width = scaled_w
        self.hitbox.height = scaled_h
        self.hitbox.x = self.x + scaled_x
        self.hitbox.y = self.y + scaled_y