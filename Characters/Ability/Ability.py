from abc import ABC, abstractmethod
import os
import re
import pygame
import Constantes as con

class Ability(ABC):
    def __init__(self, name:str, cooldown:float = 0.0, uses:int = 0, baseDamage:int = 0, level:int = 1, frames:list[str] = None, animation_speed:int = 5, scale:float = 1.0, offset_x:int = 0, offset_y:int = 0):
        self.name = name
        self.cooldown = cooldown
        self.uses = uses
        self.remaining_uses = uses
        self.cooldown_timer = 0
        self.baseDamage = baseDamage
        self.damage = baseDamage * (1 + level / 4)
        self.level = level
        self.frames = frames if frames is not None else []
        self.frame_bounds = []
        self.animation_speed = animation_speed
        self.scale = scale
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.is_attacking = False
        self.animation_timer = 0
        self.frame = 0
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        self.show_hitbox = con.SHOW_HITBOX


    def trigger_attack(self):
        """Intenta disparar el ataque. Devuelve False si está en cooldown,
        ya atacando, o sin usos restantes (hace falta ResetUses())."""
        if self.is_attacking or self.cooldown_timer > 0 or self.remaining_uses <= 0:
            return False
        self.is_attacking = True
        self.frame = 0
        self.animation_timer = 0
        self.remaining_uses -= 1
        self.cooldown_timer = self.cooldown * con.CLOCK_FPS
        return True

    def Update(self, screen, x, y, facing_right=True, character_width=0):
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1

        if not self.is_attacking:
            return

        if not self.frames:
            # Todavía no hay sprites cargados para esta habilidad: no hay nada
            # que dibujar, pero tampoco debe intentar indexar una lista vacía.
            self.is_attacking = False
            self.frame = 0
            self.hitbox = pygame.Rect(0, 0, 0, 0)
            return

        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.frame += 1

            if self.frame >= len(self.frames):
                self.is_attacking = False
                self.frame = 0
                self.hitbox = pygame.Rect(0, 0, 0, 0)
                return

        current_frame = self.frames[self.frame]
        frame_width = current_frame.get_width()

        # Mirroreado respecto al personaje: mirando a la derecha, el ataque
        # arranca "offset_x" adentro del cuerpo de Lilie (x es su borde
        # izquierdo). Mirando a la izquierda hay que reflejar eso respecto
        # a su borde DERECHO (x + character_width), no respecto a x, o el
        # ataque queda flotando separado del personaje en vez de solaparse
        # con ella igual que del otro lado.
        draw_x = x + self.offset_x if facing_right else x + character_width - self.offset_x - frame_width
        draw_y = y + self.offset_y

        if not facing_right:
            current_frame = pygame.transform.flip(current_frame, True, False)

        screen.blit(current_frame, (draw_x, draw_y))

        # Hitbox ajustada a los píxeles no transparentes del frame actual
        # (mismo criterio que el hitbox de Lilie), espejada si mira a la
        # izquierda igual que el sprite.
        bounds = self.frame_bounds[self.frame]
        bound_x = frame_width - bounds.x - bounds.width if not facing_right else bounds.x
        self.hitbox = pygame.Rect(draw_x + bound_x, draw_y + bounds.y, bounds.width, bounds.height)

        if self.show_hitbox:
            pygame.draw.rect(screen, (255, 255, 0), self.hitbox, 2)

    def ResetUses(self):
        """Restaura los usos y quita el cooldown pendiente (pensado para
        dispararse en un punto de descanso/altar, todavía no implementado)."""
        self.remaining_uses = self.uses
        self.cooldown_timer = 0

    @abstractmethod
    def name(self):
        pass
    
    def _load_frames(self, folder, prefix, count, extension="png"):
        path = os.path.join(folder)
        try:
            files = os.listdir(path)
        except FileNotFoundError:
            print(f"⚠️ No hay sprites de ataque todavía en '{path}' (arte pendiente)")
            return

        # Ordena por el número en el nombre del archivo (ataque10 va después de ataque9,
        # no antes de ataque3 como pasaría con un sort alfabético normal)
        def frame_sort_key(filename):
            match = re.search(r"(\d+)", filename)
            return (int(match.group(1)) if match else float("inf"), filename)

        for f in sorted(files, key=frame_sort_key):
            if f.lower().endswith(f".{extension}"):
                img = pygame.image.load(os.path.join(path, f)).convert_alpha()
                if self.scale != 1.0:
                    new_size = (int(img.get_width() * self.scale), int(img.get_height() * self.scale))
                    img = pygame.transform.scale(img, new_size)
                self.frames.append(img)
                self.frame_bounds.append(self._alpha_bounds(img))

    @staticmethod
    def _alpha_bounds(surface):
        rects = pygame.mask.from_surface(surface).get_bounding_rects()
        if not rects:
            return pygame.Rect(0, 0, 0, 0)
        bounds = rects[0].copy()
        for r in rects[1:]:
            bounds.union_ip(r)
        return bounds