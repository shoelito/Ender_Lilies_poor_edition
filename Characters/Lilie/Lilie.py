import pygame
import re
import json
import Constantes as con
from Characters.CharacterClass import Character

class Lilie(Character):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        with open("SavedCampaing/PreSaved1.json", "r") as f:
            self.saved = json.load(f)
        self.facing_right = True

        self.animations = {
            "idle": Character._load_frames("Lilie/Idle", "idle", 4),
            "walk": Character._load_frames("Lilie/Walk", "walk", 8),
            "jump": Character._load_frames("Lilie/Jump", "jump", 9),
            "dash": Character._load_frames("Lilie/Dash", "dash", 8),
            "pray": Character._load_frames("Lilie/Pray", "pray", 10)
        }
        
        self.pv = self.saved["player"]["pv"]
        self.attacks = self.saved["player"]["abilities_selected"]
        
        self.attacksSlot1 = self.attacks[0] 
        self.attacksSlot2 = self.attacks[1]
        self.attackSlotSelected = 1
        

        self.state = "idle"
        self.frame_index = 0
        
        
        self.anim_timer = 0
        self.anim_speed = 120
        self.gravity = con.GRAVITY
        self.vel_y = 0
        self.jumpLimit = 2 if self.saved["double_jump"] else 1
        
        self.is_jump_pressed = False
        self.is_dash_pressed = False
        self.is_jumping = False
        self.is_praying = False

        self.moving = {"left": False, "right": False, "jump": False, "dashLeft": False, "dashRight": False , "dash": False, "pray": False}
        self.speed = con.SPEED

    def update(self, dt):
        is_moving = self.moving["left"] or self.moving["right"] or self.moving["jump"] or self.moving["dashLeft"] or self.moving["dashRight"]

        new_state = "pray" if self.moving["pray"] else "dash" if self.moving["dash"] else "jump" if self.moving["jump"] else "walk" if is_moving else "idle"
        if new_state != self.state:
            self.state = new_state
            self.frame_index = 0
            self.anim_timer = 0

        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer -= self.anim_speed
            self.frame_index = (self.frame_index + 1) % len(self.animations[self.state])

        if self.moving["left"] and not self.moving["dash"] and not self.moving["pray"]:
            self.x -= self.speed
            self.facing_right = False

        if self.moving["right"] and not self.moving["dash"] and not self.moving["pray"]:
            self.x += self.speed
            self.facing_right = True

        if self.moving["dash"]:
            if self.is_jumping or self.moving["jump"]:
                if self.moving["jump"] and self.jumpLimit > 0:
                    self.jumpLimit -= 1
                self.moving["jump"] = False
                self.is_jumping = False

        if self.is_jumping and not self.moving["pray"]:
            self.moving["jump"] = True
        if self.moving["jump"] and not self.moving["pray"]:
            if self.jumpLimit > 0:
                self.vel_y = -self.speed
                self.y += self.vel_y / 7
                if self.frame_index == (len(self.animations["jump"]) // 2) - 1:
                    self.jumpLimit -= 1
                    self.moving["jump"] = False
                    self.is_jumping = False
                    self.y += self.vel_y
                    
            else:
                #debe de tocar suelo para refrescar los try de saltos
                self.moving["jump"] = False
                self.is_jumping = False

        if self.moving["pray"]:
            self.moving["jump"] = False
            self.is_jumping = False
            if self.vel_y < 0:
                self.vel_y = 0 
            self.vel_x = 0 
            if self.frame_index == (len(self.animations["pray"]) // 2) - 1:
                
                #Funcion de aumentar a vida
                
                self.moving["pray"] = False

        if self.moving["dash"]:
            
            # desactivar colicion con enemigos
            
            if self.facing_right:
                self.x += self.speed * 2
                if self.frame_index == (len(self.animations["dash"]) // 2) - 1:
                    self.moving["dash"] = False
            else:
                self.x -= self.speed * 2
                if self.frame_index == (len(self.animations["dash"]) // 2) - 1:
                    self.moving["dash"] = False
                    
        self.vel_y += self.gravity
            
        self.y += self.vel_y

        if self.y + self.height >= con.HEIGHT - 50:
            self.y = con.HEIGHT - 50 - self.height
            self.vel_y = 0
            self.jumpLimit = 2 if self.saved["double_jump"] else 1

        self.hitbox.x = self.x
        self.hitbox.y = self.y

    def draw(self, screen):
        frame, is_flip = Character._get_scaled_frame(self)
        screen.blit(frame, (self.x, self.y))
        if self.show_hitbox:
            pygame.draw.rect(screen, (0, 255, 0), self.hitbox, 2)
    
    def attack(self, attack):
        match = re.search(r'\d+', str(attack))
        if match:
            if self.attackSlotSelected == 1:
                attackSelected = int(match.group()) -1
                print(f"{attack}: {attackSelected}")

    def movements(self, actions: tuple = (None)):
        
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
        if "pray" in actions:
            if not self.is_pray_pressed:
                self.is_pray_pressed = True
                if self.vel_y == 0 and not self.moving["dash"]:
                    self.moving["pray"] = True
        else:
            self.is_pray_pressed = False
        if any("attack" in a for a in actions):
            self.attack(actions)
            
            
            