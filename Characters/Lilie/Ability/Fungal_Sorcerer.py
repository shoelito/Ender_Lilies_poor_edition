import pygame
import Constantes as con
from Characters.Ability.Ability import Ability
import json

with open("SavedCampaing/saved1.json", "r") as f:
    saved = json.load(f)


class Fungal_Sorcerer(Ability):
    def __init__(self):
        super().__init__(
            name="Fungal Sorcerer",
            cooldown=6.0,
            uses=12,
            baseDamage=50,
            level=saved["abilities"][3]["level"],
            frames=[],
            animation_speed=4,
            scale=0.35,
            offset_x=30, # Si es positivo, aparece más adelante (Y siempre toca el piso)
            anchor_once=True, # tanto la invocación como la nube quedan donde se lanzó
            damage_interval_frames=round(0.5 * con.CLOCK_FPS), # hace daño cada 0.5 segundos
            sound="ataque_veneno")
        self._load_frames()

        # Nube que queda donde se invocó (tocando el piso, como el resto),
        # usando los sprites de Assets/Lilie/Ability/Fungal_Sorcerer/Proyectil.
        self.cloud_frames = []
        self.cloud_frame_bounds = []
        self._load_cloud_frames()
        self.cloud_duration = 5 * con.CLOCK_FPS  # dura ~5 segundos

        self._in_cloud = False
        self._cloud_timer = 0
        self._cloud_frame = 0
        self._cloud_anim_timer = 0
        self._cloud_facing_right = True

    def name(self):
        return self.name

    def _apply_periodic_damage(self, enemies):
        self._damage_tick_timer += 1
        if self._damage_tick_timer >= self.damage_interval_frames:
            self._damage_tick_timer = 0
            self._periodic_hit_enemies(enemies)

    def _load_frames(self):
        super()._load_frames("Assets/Lilie/Ability/Fungal_Sorcerer", "ataque", 6)

    def _load_cloud_frames(self):
        super()._load_frames("Assets/Lilie/Ability/Fungal_Sorcerer/Proyectil", "proyectil", 6,
                              target_frames=self.cloud_frames, target_bounds=self.cloud_frame_bounds)

    def trigger_attack(self):
        fired = super().trigger_attack()
        if fired:
            self._in_cloud = False
            self._cloud_timer = 0
        return fired

    def Update(self, screen, x, y, facing_right=True, character_width=0, character_height=0, enemies=()):
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1

        if not self.is_attacking:
            return

        if self._in_cloud:
            self._update_cloud(screen, enemies)
            return

        if not self.frames:
            self._start_cloud(x, y, facing_right, character_width, character_height)
            return

        # Fase 1: animación de invocar (igual que un ataque anclado normal,
        # pero cuando termina no apaga is_attacking -> pasa a la nube).
        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.frame += 1
            if self.frame >= len(self.frames):
                self._start_cloud(x, y, facing_right, character_width, character_height)
                return

        current_frame = self.frames[self.frame]
        frame_width = current_frame.get_width()

        if self._anchor_x is None:
            self._anchor_x = x + self.offset_x if facing_right else x + character_width - self.offset_x - frame_width
            self._anchor_feet_y = y + character_height
            self._anchor_facing_right = facing_right

        # Toca los pies de Lilie en el momento de invocar (el piso si estaba
        # parada, o donde sea que estuviera si la lanzó en el aire).
        draw_y = self._anchor_feet_y - current_frame.get_height()
        draw_frame = current_frame if self._anchor_facing_right else pygame.transform.flip(current_frame, True, False)
        screen.blit(draw_frame, (self._anchor_x, draw_y))

        bounds = self.frame_bounds[self.frame]
        bound_x = frame_width - bounds.x - bounds.width if not self._anchor_facing_right else bounds.x
        self.hitbox = pygame.Rect(self._anchor_x + bound_x, draw_y + bounds.y, bounds.width, bounds.height)
        self._apply_periodic_damage(enemies)
        if self.show_hitbox:
            pygame.draw.rect(screen, (255, 255, 0), self.hitbox, 2)

    def _start_cloud(self, x, y, facing_right, character_width, character_height):
        if not self.cloud_frames:
            self.is_attacking = False
            self.frame = 0
            self.hitbox = pygame.Rect(0, 0, 0, 0)
            return

        # Si ya hay un anchor de la fase de invocación lo reusa (queda en la
        # punta de la vara, justo donde terminó de invocar); si no, lo calcula.
        if self._anchor_x is None:
            frame_width = self.cloud_frames[0].get_width()
            self._anchor_x = x + self.offset_x if facing_right else x + character_width - self.offset_x - frame_width
            self._anchor_feet_y = y + character_height
            self._anchor_facing_right = facing_right

        self._cloud_facing_right = self._anchor_facing_right
        self._in_cloud = True
        self._cloud_timer = 0
        self._cloud_frame = 0
        self._cloud_anim_timer = 0

    def _update_cloud(self, screen, enemies=()):
        self._cloud_timer += 1
        if self._cloud_timer >= self.cloud_duration:
            self.is_attacking = False
            self._in_cloud = False
            self.hitbox = pygame.Rect(0, 0, 0, 0)
            return

        self._cloud_anim_timer += 1
        if self._cloud_anim_timer >= self.animation_speed:
            self._cloud_anim_timer = 0
            self._cloud_frame = (self._cloud_frame + 1) % len(self.cloud_frames)

        current_frame = self.cloud_frames[self._cloud_frame]
        frame_width = current_frame.get_width()
        draw_y = self._anchor_feet_y - current_frame.get_height()
        draw_frame = current_frame if self._cloud_facing_right else pygame.transform.flip(current_frame, True, False)
        screen.blit(draw_frame, (self._anchor_x, draw_y))

        bounds = self.cloud_frame_bounds[self._cloud_frame]
        bound_x = frame_width - bounds.x - bounds.width if not self._cloud_facing_right else bounds.x
        self.hitbox = pygame.Rect(self._anchor_x + bound_x, draw_y + bounds.y, bounds.width, bounds.height)
        self._apply_periodic_damage(enemies)
        if self.show_hitbox:
            pygame.draw.rect(screen, (255, 255, 0), self.hitbox, 2)
