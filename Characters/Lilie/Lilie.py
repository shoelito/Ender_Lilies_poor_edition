import pygame
import re
import json
import Constantes as con
import Sonidos
from Characters.CharacterClass import Character
from Characters.Lilie.Ability.Umbral_Knight import Umbral_Knight
from Characters.Lilie.Ability.Guardian_Siegrid import Guardian_Siegrid
from Characters.Lilie.Ability.Fungal_Sorcerer import Fungal_Sorcerer
from Characters.Lilie.Ability.Floral_Sorceress import Floral_Sorceress
from Characters.Lilie.Ability.Cliffside_Hamlet_Youth import Cliffside_Hamlet_Youth
from Characters.Lilie.Ability.Dark_Witch_Eleine import Dark_Witch_Eleine

class Lilie(Character):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        with open("SavedCampaing/PreSaved1.json", "r") as f:
            self.saved = json.load(f)
        self.facing_right = True

        self.animations = {
            "idle": Character._load_frames("Lilie/Idle", "idle", 4),
            "walk": Character._load_frames("Lilie/Walk", "walk", 8),
            "jump": Character._load_frames("Lilie/Jump", "jump", 10),
            "dash": Character._load_frames("Lilie/Dash", "dash", 8),
            "pray": Character._load_frames("Lilie/Pray", "rezar", 10)
        }

        # Bounding box (en coordenadas del frame sin escalar) de los píxeles
        # no transparentes de cada frame, para que el hitbox siga el dibujo
        # real de Lilie en vez de todo el lienzo width x height.
        self.animation_bounds = {
            state: [Character._alpha_bounds(frame) for frame in frames]
            for state, frames in self.animations.items()
        }

        # Salud. El "pv" del save es la vida máxima; se arranca a tope.
        self.max_pv = self.saved["player"]["pv"]
        self.pv = self.max_pv

        # Plegarias: cargas de curación que se gastan al rezar y se reponen en
        # los puntos de descanso. El save manda, pero nunca por encima del tope.
        self.max_healing_prayers = min(
            self.saved.get("healing_prayers", con.MAX_HEALING_PRAYERS),
            con.MAX_HEALING_PRAYERS)
        self.healing_prayers = self.max_healing_prayers

        self.invuln_timer = 0      # ms de invulnerabilidad que le quedan
        self.hurt_timer = 0        # ms de destello rojo
        self.dash_grace_timer = 0  # colita de invulnerabilidad al salir del dash
        self.is_dead = False


        ability_map = {
            "umbral_knight": Umbral_Knight,
            "guardian_siegrid": Guardian_Siegrid,
            "fungal_sorcerer": Fungal_Sorcerer,
            "floral_sorcerer": Floral_Sorceress,
            "cliffside_hamlet_youth": Cliffside_Hamlet_Youth,
            "dark_witch_eleine": Dark_Witch_Eleine
        }
        
        self.attacks = []
        for slot in self.saved["player"]["abilities_selected"]:
            slot_abilities = []
            for ability_name in slot:
                if ability_name in ability_map:
                    slot_abilities.append(ability_map[ability_name]())
            self.attacks.append(slot_abilities)
            
        self.slotSelected = 0
        

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
        self.is_pray_pressed = False
        self.is_slot_pressed = False
        self.is_attack_pressed = False

        self.moving = {"left": False, "right": False, "jump": False, "dashLeft": False, "dashRight": False , "dash": False, "pray": False}
        self.speed = con.SPEED

    # ------------------------------------------------------ salud y plegarias

    @property
    def is_invulnerable(self):
        """No recibe daño ni por golpe ni por contacto mientras: arrastra los
        i-frames del golpe anterior, o está esquivando (el dash la vuelve
        intangible de principio a fin, más una colita de gracia al salir)."""
        return (self.invuln_timer > 0
                or self.moving["dash"]
                or self.dash_grace_timer > 0)

    def take_damage(self, amount):
        """Aplica daño. Devuelve True solo si el golpe entró de verdad: durante
        los i-frames, esquivando o ya muerta, se ignora."""
        if self.is_dead or self.is_invulnerable or amount <= 0:
            return False

        self.pv = max(0, self.pv - int(amount))
        self.invuln_timer = con.HURT_INVULN_MS
        self.hurt_timer = con.HURT_FLASH_MS

        # Rezar deja expuesta: el golpe corta la plegaria, pero como no llegó a
        # curar tampoco se gasta la carga.
        if con.PRAYER_CANCELLED_BY_DAMAGE and self.moving["pray"]:
            self.moving["pray"] = False

        if self.pv <= 0:
            self._die()
        return True

    def _die(self):
        self.is_dead = True
        self.pv = 0
        for key in self.moving:
            self.moving[key] = False
        self.state = "idle"
        self.frame_index = 0
        self.anim_timer = 0

    def heal(self, amount):
        """Cura sin pasarse del máximo. Devuelve cuánta vida se recuperó."""
        if self.is_dead or amount <= 0:
            return 0
        antes = self.pv
        self.pv = min(self.max_pv, self.pv + int(amount))
        return self.pv - antes

    def can_pray(self):
        """Solo se reza con cargas, en el piso, quieta y viva."""
        return (not self.is_dead
                and self.healing_prayers > 0
                and not self.moving["pray"]
                and not self.moving["dash"]
                and self.vel_y == 0)

    def _finish_prayer(self):
        """Momento exacto de la curación, a mitad de la animación de rezo."""
        if self.healing_prayers <= 0:
            return
        self.healing_prayers -= 1
        curado = self.heal(self.max_pv * con.PRAYER_HEAL_RATIO)
        print(f"Plegaria: +{curado} PV ({self.pv}/{self.max_pv}) | "
              f"plegarias restantes {self.healing_prayers}/{self.max_healing_prayers}")

    def rest(self):
        """Punto de descanso: cura del todo y repone todas las plegarias."""
        self.pv = self.max_pv
        self.healing_prayers = self.max_healing_prayers
        self.is_dead = False
        self.invuln_timer = 0
        self.hurt_timer = 0

    # ---------------------------------------------------------------- update

    def update(self, dt, colisiones=None):
        if colisiones is None:
            colisiones = []
        
        prev_x = self.x
        
        self.invuln_timer = max(0, self.invuln_timer - dt)
        self.hurt_timer = max(0, self.hurt_timer - dt)
        self.dash_grace_timer = max(0, self.dash_grace_timer - dt)

        if self.is_dead:
            # Se queda tirada donde cayó: sin input, sin física, sin ataques.
            self._sync_hitbox()
            return

        is_moving = self.moving["left"] or self.moving["right"] or self.moving["jump"] or self.moving["dashLeft"] or self.moving["dashRight"]

        is_in_air = getattr(self, 'on_ground', False) == False
        new_state = "pray" if self.moving["pray"] else "dash" if self.moving["dash"] else "jump" if (self.moving["jump"] or is_in_air) else "walk" if is_moving else "idle"
        if new_state != self.state:
            self.state = new_state
            self.frame_index = 0
            self.anim_timer = 0

        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer -= self.anim_speed
            self.frame_index = (self.frame_index + 1) % len(self.animations[self.state])

        if self.is_rooted():
            # Una habilidad con roots_caster (ej. Umbral Knight) la tiene
            # congelada: no se mueve en ningún eje mientras dure el ataque,
            # esté en el aire o en el piso (la animación de Lilie sigue
            # corriendo arriba, solo se frena la posición).
            self._sync_hitbox()
            return

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
                self.y += self.vel_y / 6
                if self.frame_index >= (len(self.animations["jump"]) // 2) - 1:
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
                self._finish_prayer()
                self.moving["pray"] = False

        if self.moving["dash"]:
            # Esquivar la vuelve intangible: se refresca la invulnerabilidad en
            # cada frame del dash, así sigue activa la colita al terminarlo.
            self.dash_grace_timer = con.DASH_INVULN_GRACE_MS

            if self.facing_right:
                self.x += self.speed * 2
                if self.frame_index == (len(self.animations["dash"]) // 2) - 1:
                    self.moving["dash"] = False
            else:
                self.x -= self.speed * 2
                if self.frame_index == (len(self.animations["dash"]) // 2) - 1:
                    self.moving["dash"] = False
                    
        # --- COLISIONES X ---
        # Usamos un rectángulo lógico fijo para el mapa, para que la animación no cause vibraciones.
        # Quitamos márgenes horizontales (ej. 30px) para que no choque con paredes estando lejos.
        # La holgura se le saca a la cabeza, nunca a los pies: el borde de abajo
        # sigue siendo y+height porque es lo que apoya en el piso. Sin ella, un
        # pasillo que mide justo lo mismo que ella es infranqueable (en
        # mapa_zona_2 hay uno de 110px y el cuerpo mide 110), y a la larga la
        # frenaba antes de llegar al nivel siguiente.
        holgura = con.HOLGURA_TECHO
        logical_rect = pygame.Rect(self.x + 30, self.y + 10 + holgura,
                                   self.width - 60, self.height - 10 - holgura)
        
        for rect in colisiones:
            if logical_rect.colliderect(rect):
                if self.x > prev_x: # Se movió a la derecha
                    self.x -= (logical_rect.right - rect.left)
                    logical_rect.x -= (logical_rect.right - rect.left)
                elif self.x < prev_x: # Se movió a la izquierda
                    self.x += (rect.right - logical_rect.left)
                    logical_rect.x += (rect.right - logical_rect.left)

        # --- MOVIMIENTO Y ---
        self.vel_y += self.gravity
        self.y += self.vel_y
        logical_rect.y += self.vel_y

        # --- COLISIONES Y ---
        toco_suelo = False
        for rect in colisiones:
            if logical_rect.colliderect(rect):
                if self.vel_y > 0: # Cayendo, choca con piso
                    self.y -= (logical_rect.bottom - rect.top)
                    logical_rect.y -= (logical_rect.bottom - rect.top)
                    self.vel_y = 0
                    toco_suelo = True
                elif self.vel_y < 0: # Subiendo, choca con techo
                    self.y += (rect.bottom - logical_rect.top)
                    logical_rect.y += (rect.bottom - logical_rect.top)
                    self.vel_y = 0

        # Evitar caer infinitamente si sale del mapa
        if self.y > 5000:
            self.y = 5000
            self.vel_y = 0
            toco_suelo = True

        if toco_suelo:
            self.jumpLimit = 2 if self.saved["double_jump"] else 1

        self.on_ground = toco_suelo

        # El hitbox se sincronizaba sólo en las salidas tempranas (muerta o
        # inmovilizada), así que en el camino normal se quedaba clavado donde
        # se construyó a Lilie. Mientras el mundo medía una pantalla casi no se
        # notaba; con el mapa de Tiled sí, porque la cámara sigue este rect y
        # se quedaba mirando siempre el mismo rincón del nivel.
        self._sync_hitbox()

    def draw(self, screen, enemies=()):
        frame, is_flip = Character._get_scaled_frame(self)

        if self.is_dead:
            # Silueta apagada donde cayó.
            frame = frame.copy()
            frame.fill((90, 90, 110), special_flags=pygame.BLEND_RGB_MULT)
        elif self.hurt_timer > 0:
            frame = frame.copy()
            frame.fill((255, 70, 70), special_flags=pygame.BLEND_RGB_ADD)
        elif self.moving["dash"]:
            # Semitransparente mientras esquiva, para que se lea que en ese
            # momento los golpes la atraviesan.
            frame = frame.copy()
            frame.set_alpha(con.DASH_ALPHA)

        # Terminado el destello, parpadea lo que queda de invulnerabilidad.
        parpadeo = (self.invuln_timer > 0 and self.hurt_timer <= 0
                    and (self.invuln_timer // 60) % 2 == 0)
        if not parpadeo:
            screen.blit(frame, (self.x, self.y))

        if self.show_hitbox:
            pygame.draw.rect(screen, (0, 255, 0), self.hitbox, 2)

        if self.is_dead:
            return

        for attack in self.attacks[self.slotSelected]:
            attack.Update(screen, self.x, self.y, self.facing_right, self.width, self.height, enemies)

    def draw_hud(self, screen):
        """Barra de vida y contador de plegarias, arriba a la izquierda."""
        m = con.HUD_MARGIN
        ancho, alto = 320, 16

        pygame.draw.rect(screen, (12, 10, 14), (m - 2, m - 2, ancho + 4, alto + 4))
        pygame.draw.rect(screen, (52, 18, 22), (m, m, ancho, alto))
        ratio = self.pv / self.max_pv if self.max_pv else 0
        if ratio > 0:
            color = (196, 52, 56) if ratio > 0.3 else (226, 96, 60)
            pygame.draw.rect(screen, color, (m, m, int(ancho * ratio), alto))
        pygame.draw.rect(screen, (150, 140, 130), (m, m, ancho, alto), 1)

        fuente = pygame.font.Font(None, 22)
        screen.blit(fuente.render(f"{self.pv}/{self.max_pv}", True, (222, 216, 204)),
                    (m + ancho + 10, m))

        # Plegarias: una cuenta por carga, apagada si ya se gastó.
        cy = m + alto + 16
        for i in range(self.max_healing_prayers):
            cx = m + 8 + i * 22
            disponible = i < self.healing_prayers
            pygame.draw.circle(screen, (206, 198, 176) if disponible else (58, 54, 58),
                               (cx, cy), 7)
            pygame.draw.circle(screen, (150, 140, 130), (cx, cy), 7, 1)


    def attack(self, attack, screen):
        match = re.search(r'\d+', str(attack))
        if match:
            attackSelected = int(match.group()) -1
            try:
                ability = self.attacks[self.slotSelected][attackSelected]
                if not ability.trigger_attack():
                    print(f"{ability.name}: sin usos o en cooldown ({ability.remaining_uses}/{ability.uses} usos)")
            except IndexError:
                print("No hay ataque seleccionado")

    def is_rooted(self):
        """True si alguna habilidad del slot activo la tiene inmovilizada
        mientras dura su ataque (ej. Umbral Knight)."""
        return any(a.roots_caster and a.is_attacking for a in self.attacks[self.slotSelected])

    def movements(self, actions: tuple = (None), screen = None ):
        if self.is_dead:
            return

        rooted = self.is_rooted()

        if "left" in actions and not rooted:
            self.moving["left"] = True
        else:
            self.moving["left"] = False
        if "right" in actions and not rooted:
            self.moving["right"] = True
        else:
            self.moving["right"] = False
        if "jump" in actions and not rooted:
            if not self.is_jump_pressed:
                self.is_jump_pressed = True
                self.is_jumping = True
                # Solo suena si de verdad le queda salto; si no, el botón no
                # hace nada y un sonido ahí engañaría.
                if self.jumpLimit > 0:
                    Sonidos.reproducir("salto")
        else:
            self.is_jump_pressed = False
        if "dash" in actions and not rooted:
            if not self.is_dash_pressed:
                self.is_dash_pressed = True
                self.moving["dash"] = True
                Sonidos.reproducir("dash")
        else:
            self.is_dash_pressed = False
        if "pray" in actions:
            if not self.is_pray_pressed:
                self.is_pray_pressed = True
                if self.can_pray():
                    self.moving["pray"] = True
                    # Se arranca la animación desde cero a mano: si la anterior
                    # ya era "pray", update() no la reiniciaría y la curación
                    # (que cae en el frame del medio) dispararía al instante.
                    self.state = "pray"
                    self.frame_index = 0
                    self.anim_timer = 0
                    Sonidos.reproducir("rezar")
                elif self.healing_prayers <= 0:
                    print("Sin plegarias: hay que descansar para reponerlas")
        else:
            self.is_pray_pressed = False
        attack_action = next((a for a in actions if "attack" in a), None)
        if attack_action:
            if not self.is_attack_pressed:
                self.is_attack_pressed = True
                self.attack(attack_action, screen)
        else:
            self.is_attack_pressed = False
            
        if "changeSlot" in actions:
            if not self.is_slot_pressed:
                self.is_slot_pressed = True
                self.slotSelected = (self.slotSelected + 1) % 2
                print(f"Slot seleccionado: {self.slotSelected}")
        else:
            self.is_slot_pressed = False