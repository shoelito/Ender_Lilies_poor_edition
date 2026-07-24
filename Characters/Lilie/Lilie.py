import pygame
import os
import json
import Constantes as con
from Characters.CharacterClass import Character

with open("SavedCampaing/saved1.json", "r") as f:
    saved = json.load(f)

class Lilie(Character):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.facing_right = True

        self.animations = {
            "idle": Character._load_frames("Lilie/Idle", "idle", 4),
            "walk": Character._load_frames("Lilie/Walk", "walk", 8),
            "jump": Character._load_frames("Lilie/Jump", "jump", 9),
            "dash": Character._load_frames("Lilie/Dash", "dash", 8)
        }

        self.state = "idle"
        self.frame_index = 0
        self.anim_timer = 0
        self.anim_speed = 120
        self.gravity = con.GRAVITY
        self.vel_y = 0
        self.jumpLimit = 2 if saved["double_jump"] else 1
        self.is_jump_pressed = False
        self.is_dash_pressed = False
        self.is_jumping = False

        self.moving = {"left": False, "right": False, "jump": False, "dashLeft": False, "dashRight": False , "dash": False}
        self.speed = con.SPEED

    def update(self, dt):
        is_moving = self.moving["left"] or self.moving["right"] or self.moving["jump"] or self.moving["dashLeft"] or self.moving["dashRight"]

        new_state = "dash" if self.moving["dash"] else "jump" if self.moving["jump"] else "walk" if is_moving else "idle"
        if new_state != self.state:
            self.state = new_state
            self.frame_index = 0
            self.anim_timer = 0

        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer -= self.anim_speed
            self.frame_index = (self.frame_index + 1) % len(self.animations[self.state])

        if self.moving["left"] and not self.moving["dash"]:
            self.x -= self.speed
            self.facing_right = False

        if self.moving["right"] and not self.moving["dash"]:
            self.x += self.speed
            self.facing_right = True

        if self.is_jumping:
            self.moving["jump"] = True
        if self.moving["jump"]:
            if self.jumpLimit > 0:
                self.vel_y = -self.speed
                self.y += self.vel_y
                if self.frame_index == (len(self.animations["jump"]) // 2) - 1:
                    self.jumpLimit -= 1
                    self.moving["jump"] = False
                    self.is_jumping = False
                    self.y += self.vel_y
                    
            else:
                #debe de tocar suelo para refrescar los try de saltos
                self.moving["jump"] = False
                self.is_jumping = False

        if self.moving["dash"]:
            if self.facing_right:
                self.x += self.speed * 2
                if self.frame_index == (len(self.animations["dash"]) // 2) - 1:
                    self.moving["dash"] = False
                    self.vel_y = 0
            else:
                self.x -= self.speed * 2
                if self.frame_index == (len(self.animations["dash"]) // 2) - 1:
                    self.moving["dash"] = False
                    self.vel_y = 0
        
        self.vel_y += self.gravity
        self.y += self.vel_y

        if self.y + self.height >= con.HEIGHT - 50:
            self.y = con.HEIGHT - 50 - self.height
            self.vel_y = 0
            self.jumpLimit = 2 if saved["double_jump"] else 1

        self.hitbox.x = self.x
        self.hitbox.y = self.y

    def draw(self, screen):
        frame, is_flip = Character._get_scaled_frame(self)
        screen.blit(frame, (self.x, self.y))
        if self.show_hitbox:
            pygame.draw.rect(screen, (0, 255, 0), self.hitbox, 2)
        
    def groundCollision(self):
        pass

    def move(self, actions):
        print(self.jumpLimit)
        if "left" in actions:
            self.moving["left"] = True
        else:
            self.moving["left"] = False
        if "right" in actions:
            self.moving["right"] = True
        else:
            self.moving["right"] = False
        if "jump" in actions:
            if not self.is_jump_pressed:
                self.is_jump_pressed = True
                self.is_jumping = True
        else:
            self.is_jump_pressed = False
        if "dash" in actions:
            if not self.is_dash_pressed:
                self.is_dash_pressed = True
                self.moving["dash"] = True
        else:
            self.is_dash_pressed = False