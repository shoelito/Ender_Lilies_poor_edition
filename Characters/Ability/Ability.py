from abc import ABC, abstractmethod
import os
import re
import pygame
import Constantes as con
import Sonidos

class Ability(ABC):
    def __init__(self, name:str, cooldown:float = 0.0, uses:int = 0, baseDamage:int = 0, level:int = 1, frames:list[str] = None, animation_speed:int = 5, scale:float = 1.0, offset_x:int = 0, offset_y:int = 0,
                 is_projectile:bool = False, projectile_speed:float = 0.0, projectile_gravity:float = 0.0, projectile_launch_vy:float = 0.0,
                 anchor_once:bool = False, loop_count:int = 1, duration_frames:int = None, roots_caster:bool = False,
                 damage_on_loop:bool = False, damage_interval_frames:int = None,
                 sound:str = None, loop_sound:str = None, impact_sound:str = None):
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


        self.is_projectile = is_projectile
        self.projectile_speed = projectile_speed
        self.projectile_gravity = projectile_gravity
        self.projectile_launch_vy = projectile_launch_vy
        self.projectile_x = 0.0
        self.projectile_y = 0.0
        self.projectile_vx = 0.0
        self.projectile_vy = 0.0
        self._projectile_spawned = False


        self.anchor_once = anchor_once
        self.loop_count = loop_count
        self.duration_frames = duration_frames
        self.roots_caster = roots_caster
        self._anchor_x = None
        self._anchor_feet_y = None
        self._anchor_facing_right = True
        self._loops_done = 0
        self._duration_timer = 0


        self._hit_targets = set()

        self.damage_on_loop = damage_on_loop
        self.damage_interval_frames = damage_interval_frames
        self._damage_tick_timer = 0

        self.sound = sound
        self.loop_sound = loop_sound
        self.impact_sound = impact_sound

    def trigger_attack(self):
        if self.is_attacking or self.cooldown_timer > 0 or self.remaining_uses <= 0:
            return False
        self.is_attacking = True
        self.frame = 0
        self.animation_timer = 0
        self._projectile_spawned = False
        self._anchor_x = None
        self._anchor_feet_y = None
        self._loops_done = 0
        self._duration_timer = 0
        self._hit_targets = set()
        self._damage_tick_timer = 0
        self.remaining_uses -= 1
        self.cooldown_timer = self.cooldown * con.CLOCK_FPS

        if self.sound:
            Sonidos.reproducir(self.sound)
        if self.loop_sound:
            Sonidos.reproducir(self.loop_sound)  
        return True

    def _hit_enemies(self, enemies):
        hit_any = False
        for enemy in enemies:
            if enemy in self._hit_targets or getattr(enemy, "state", None) == "dead":
                continue
            if self.hitbox.colliderect(enemy.hitbox):
                enemy.take_damage(self.damage)
                self._hit_targets.add(enemy)
                hit_any = True
        return hit_any

    def _periodic_hit_enemies(self, enemies):
        for enemy in enemies:
            if getattr(enemy, "state", None) == "dead":
                continue
            if self.hitbox.colliderect(enemy.hitbox):
                enemy.take_damage(self.damage)

    def Update(self, screen, x, y, facing_right=True, character_width=0, character_height=0, enemies=()):
        if self.cooldown_timer > 0:
            self.cooldown_timer -= 1

        if not self.is_attacking:
            return

        if not self.frames:
            self.is_attacking = False
            self.frame = 0
            self.hitbox = pygame.Rect(0, 0, 0, 0)
            return

        if self.is_projectile:
            self._update_projectile(screen, x, y, facing_right, character_width, character_height, enemies)
            return

        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.frame += 1

            if self.frame >= len(self.frames):
                self.frame = 0
                self._loops_done += 1
                if self.damage_on_loop:
                    self._periodic_hit_enemies(enemies)
                if self.duration_frames is None and self._loops_done >= self.loop_count:
                    self.is_attacking = False
                    self.hitbox = pygame.Rect(0, 0, 0, 0)
                    return
                # Quedan vueltas: suena el arranque de la siguiente. (La
                # primera ya sonó en trigger_attack.)
                if self.loop_sound:
                    Sonidos.reproducir(self.loop_sound)

        if self.duration_frames is not None:
            self._duration_timer += 1
            if self._duration_timer >= self.duration_frames:
                self.is_attacking = False
                self.frame = 0
                self.hitbox = pygame.Rect(0, 0, 0, 0)
                return

        current_frame = self.frames[self.frame]
        frame_width = current_frame.get_width()


        feet_y = y + character_height
        if self.anchor_once:
            if self._anchor_x is None:
                self._anchor_x = x + self.offset_x if facing_right else x + character_width - self.offset_x - frame_width
                self._anchor_feet_y = feet_y
                self._anchor_facing_right = facing_right
            draw_x = self._anchor_x
            draw_y = self._anchor_feet_y - current_frame.get_height()
            effective_facing_right = self._anchor_facing_right
        else:
            draw_x = x + self.offset_x if facing_right else x + character_width - self.offset_x - frame_width
            draw_y = feet_y - current_frame.get_height()
            effective_facing_right = facing_right

        if not effective_facing_right:
            current_frame = pygame.transform.flip(current_frame, True, False)

        screen.blit(current_frame, (draw_x, draw_y))

        bounds = self.frame_bounds[self.frame]
        bound_x = frame_width - bounds.x - bounds.width if not effective_facing_right else bounds.x
        self.hitbox = pygame.Rect(draw_x + bound_x, draw_y + bounds.y, bounds.width, bounds.height)

        if self.damage_on_loop:
            pass  # ya se aplicó arriba, al completar cada vuelta
        elif self.damage_interval_frames is not None:
            self._damage_tick_timer += 1
            if self._damage_tick_timer >= self.damage_interval_frames:
                self._damage_tick_timer = 0
                self._periodic_hit_enemies(enemies)
        else:
            self._hit_enemies(enemies)

        if self.show_hitbox:
            pygame.draw.rect(screen, (255, 255, 0), self.hitbox, 2)

    def _update_projectile(self, screen, x, y, facing_right, character_width, character_height, enemies):
        if not self._projectile_spawned:
            spawn_frame_width = self.frames[0].get_width()
            spawn_frame_height = self.frames[0].get_height()
            spawn_x = x + self.offset_x if facing_right else x + character_width - self.offset_x - spawn_frame_width
            self.projectile_x = float(spawn_x)
            self.projectile_y = float((y + character_height) - spawn_frame_height)  # arranca en los pies de Lilie
            self.projectile_vx = self.projectile_speed if facing_right else -self.projectile_speed
            self.projectile_vy = self.projectile_launch_vy
            self._projectile_spawned = True

        self.animation_timer += 1
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.frame = (self.frame + 1) % len(self.frames)

        self.projectile_x += self.projectile_vx
        self.projectile_vy += self.projectile_gravity
        self.projectile_y += self.projectile_vy

        current_frame = self.frames[self.frame]
        frame_width = current_frame.get_width()
        frame_height = current_frame.get_height()
        bounds = self.frame_bounds[self.frame]
        bound_x = frame_width - bounds.x - bounds.width if not facing_right else bounds.x
        self.hitbox = pygame.Rect(round(self.projectile_x + bound_x), round(self.projectile_y + bounds.y), bounds.width, bounds.height)

        hit_wall = self.projectile_x < -frame_width or self.projectile_x > con.WIDTH
        hit_ground = self.projectile_gravity > 0 and self.projectile_y + frame_height >= con.GROUND_Y
        hit_enemy = self._hit_enemies(enemies)

        if hit_wall or hit_ground or hit_enemy:
            if self.impact_sound:
                Sonidos.reproducir(self.impact_sound)
            self.is_attacking = False
            self.frame = 0
            self.hitbox = pygame.Rect(0, 0, 0, 0)
            return

        draw_frame = current_frame if facing_right else pygame.transform.flip(current_frame, True, False)
        screen.blit(draw_frame, (round(self.projectile_x), round(self.projectile_y)))

        if self.show_hitbox:
            pygame.draw.rect(screen, (255, 255, 0), self.hitbox, 2)

    def ResetUses(self):
        self.remaining_uses = self.uses
        self.cooldown_timer = 0

    @abstractmethod
    def name(self):
        pass
    
    def _load_frames(self, folder, prefix, count, extension="png", target_frames=None, target_bounds=None):
        frames_out = self.frames if target_frames is None else target_frames
        bounds_out = self.frame_bounds if target_bounds is None else target_bounds

        path = os.path.join(folder)
        try:
            files = os.listdir(path)
        except FileNotFoundError:
            print(f"No hay sprites de ataque todavía en '{path}'")
            return

        def frame_sort_key(filename):
            match = re.search(r"(\d+)", filename)
            return (int(match.group(1)) if match else float("inf"), filename)

        for f in sorted(files, key=frame_sort_key):
            if f.lower().endswith(f".{extension}"):
                img = pygame.image.load(os.path.join(path, f)).convert_alpha()
                if self.scale != 1.0:
                    new_size = (int(img.get_width() * self.scale), int(img.get_height() * self.scale))
                    img = pygame.transform.scale(img, new_size)
                frames_out.append(img)
                bounds_out.append(self._alpha_bounds(img))

    @staticmethod
    def _alpha_bounds(surface):
        rects = pygame.mask.from_surface(surface).get_bounding_rects()
        if not rects:
            return pygame.Rect(0, 0, 0, 0)
        bounds = rects[0].copy()
        for r in rects[1:]:
            bounds.union_ip(r)
        return bounds