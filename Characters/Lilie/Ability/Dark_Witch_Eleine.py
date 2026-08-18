import pygame
import Constantes as con
import Mundo
from Characters.Ability.Ability import Ability
import json

with open("SavedCampaing/saved1.json", "r") as f:
    saved = json.load(f)


class Dark_Witch_Eleine(Ability):
    def __init__(self):
        super().__init__(
            name="Dark Witch Eleine",
            cooldown=0.0,
            uses=70,
            baseDamage=50,
            level=saved["abilities"][5]["level"],
            frames=[],
            animation_speed=4,
            scale=0.35,
            offset_x=30, # Si es positivo, aparece más adelante (Y siempre toca el piso)
            anchor_once=True, # la invocación queda donde se lanzó, no sigue a Lilie
            sound="tiro_magia")
        self._load_frames()

        # El proyectil que realmente viaja es la esfera carmesí de
        # Assets/.../Dark_Witch_Eleine/proyectil; "carmesi*" en la raíz es
        # solo la animación de invocar.
        self.orb_frames = []
        self.orb_frame_bounds = []
        self._load_orb_frames()
        self.orb_speed = 10  # sin peso físico: vuela recto hasta chocar

        self._in_flight = False
        self._orb_frame = 0
        self._orb_anim_timer = 0
        self._orb_x = 0.0
        self._orb_y = 0.0
        self._orb_vx = 0.0

    def name(self):
        return self.name

    def _load_frames(self):
        super()._load_frames("Assets/Lilie/Ability/Dark_Witch_Eleine", "carmesi", 8)

    def _load_orb_frames(self):
        super()._load_frames("Assets/Lilie/Ability/Dark_Witch_Eleine/proyectil", "proyectil", 4,
                              target_frames=self.orb_frames, target_bounds=self.orb_frame_bounds)

    def trigger_attack(self):
        fired = super().trigger_attack()
        if fired:
            self._in_flight = False
        return fired

    def Update(self, screen, x, y, facing_right=True, character_width=0, character_height=0, enemies=()):
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1

        if not self.is_attacking:
            return

        if self._in_flight:
            self._update_orb(screen, enemies)
            return

        if not self.frames:
            self._launch_orb(x, y, facing_right, character_width, character_height)
            return

        # Fase 1: animación de invocar (igual que un ataque anclado normal,
        # pero cuando termina no apaga is_attacking -> lanza la esfera).
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.frame += 1
            if self.frame >= len(self.frames):
                self._launch_orb(x, y, facing_right, character_width, character_height)
                return

        current_frame = self.frames[self.frame]
        frame_width = current_frame.get_width()

        if self._anchor_x is None:
            self._anchor_x = x + self.offset_x if facing_right else x + character_width - self.offset_x - frame_width
            self._anchor_feet_y = y + character_height
            self._anchor_facing_right = facing_right

        draw_y = self._anchor_feet_y - current_frame.get_height()
        draw_frame = current_frame if self._anchor_facing_right else pygame.transform.flip(current_frame, True, False)
        screen.blit(draw_frame, (self._anchor_x, draw_y))

        bounds = self.frame_bounds[self.frame]
        bound_x = frame_width - bounds.x - bounds.width if not self._anchor_facing_right else bounds.x
        self.hitbox = pygame.Rect(self._anchor_x + bound_x, draw_y + bounds.y, bounds.width, bounds.height)
        self._hit_enemies(enemies)
        if self.show_hitbox:
            pygame.draw.rect(screen, (255, 255, 0), self.hitbox, 2)

    def _launch_orb(self, x, y, facing_right, character_width, character_height):
        if not self.orb_frames:
            self.is_attacking = False
            self.frame = 0
            self.hitbox = pygame.Rect(0, 0, 0, 0)
            return

        # Si ya hay un anchor de la fase de invocación lo reusa (la esfera
        # sale del mismo punto donde terminó de invocar); si no, lo calcula.
        if self._anchor_x is None:
            frame_width = self.orb_frames[0].get_width()
            self._anchor_x = x + self.offset_x if facing_right else x + character_width - self.offset_x - frame_width
            self._anchor_feet_y = y + character_height
            self._anchor_facing_right = facing_right

        self._orb_x = float(self._anchor_x)
        self._orb_y = float(self._anchor_feet_y - self.orb_frames[0].get_height())
        self._orb_vx = self.orb_speed if self._anchor_facing_right else -self.orb_speed
        self._orb_frame = 0
        self._orb_anim_timer = 0
        self._in_flight = True

    def _update_orb(self, screen, enemies):
        self._orb_anim_timer += 1
        if self._orb_anim_timer >= self.animation_speed:
            self._orb_anim_timer = 0
            self._orb_frame = (self._orb_frame + 1) % len(self.orb_frames)

        self._orb_x += self._orb_vx

        current_frame = self.orb_frames[self._orb_frame]
        frame_width = current_frame.get_width()
        bounds = self.orb_frame_bounds[self._orb_frame]
        bound_x = frame_width - bounds.x - bounds.width if not self._anchor_facing_right else bounds.x
        self.hitbox = pygame.Rect(round(self._orb_x + bound_x), round(self._orb_y + bounds.y), bounds.width, bounds.height)

        # "Choca con una pared": todavía no hay geometría de nivel, así que
        # los bordes de pantalla hacen de pared por ahora.
        hit_wall = self._orb_x < -frame_width or self._orb_x > Mundo.ancho
        hit_enemy = self._hit_enemies(enemies)

        if hit_wall or hit_enemy:
            self.is_attacking = False
            self._in_flight = False
            self.hitbox = pygame.Rect(0, 0, 0, 0)
            return

        draw_frame = current_frame if self._anchor_facing_right else pygame.transform.flip(current_frame, True, False)
        screen.blit(draw_frame, (round(self._orb_x), round(self._orb_y)))

        if self.show_hitbox:
            pygame.draw.rect(screen, (255, 255, 0), self.hitbox, 2)
