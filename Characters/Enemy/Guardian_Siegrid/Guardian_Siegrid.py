"""Guardian Siegrid, primera jefa del juego."""
import os
import random

import pygame

import Constantes as con
import Sonidos
from Characters.CharacterClass import Character
from Characters.Enemy.EnemyClass import Enemy
from Characters.Enemy.Guardian_Siegrid.Move import Move


class Guardian_Siegrid(Enemy):
    """Guardiana Siegrid, primer jefe de Ender Lilies.

    Monja del Sacro Recinto que se quedó custodiando a Lilie hasta que la
    Lluvia de la Muerte la convirtió en Blighted. Pelea con un mangual (bola
    y cadena) y su forma corrupta tiene alas de Blight.

    Fase I (wiki):
      - Salta girando el mangual y lo descarga hacia adelante al aterrizar.
      - Da un mangualazo al frente.
      - Gira el mangual a su alrededor tres veces.

    Al ~10% de vida se transforma, RECUPERA TODA LA VIDA y pasa a:
      - Alza la mano y estoca al frente; puede encadenar un segundo tajo.
      - Clava las manos en el suelo, embiste y remata con un tajo ascendente.
      - Salta y se deja caer aplastando el suelo.

    La wiki le suma un cuarto ataque en esta forma, un golpe hacia atrás
    cuando Lilie le queda a la espalda, pero no hay animación de golpe
    trasero: el sprite atacaba al frente mientras el daño ocurría detrás, y
    eso es ilegible para el jugador. En su lugar, quedarle atrás la obliga a
    girar, y ese giro es la ventana para castigarla.
    """

    SPRITE_FOLDER = "Enemy/Guardian_Siegrid"
    VIDEO_MUERTE = "siegrid"

    # -------------------------------------------------------- fase I: mangual
    FLAIL_SWING = Move("flail_swing", "flail_swing",
                       telegraph=1040, windup=460, active=240, recovery=560,
                       damage=22, reach=105, height=140, advance=3,
                       min_range=0, max_range=330, cooldown=2400,
                       hit_sound="siegrid_mangual")

    # "Spins her flail around her three times": tres vueltas completas, el
    # hitbox abarca los dos costados, así que quedarse pegada no salva.
    FLAIL_SPIN = Move("flail_spin", "flail_spin",
                      telegraph=980, windup=520, active=1080, recovery=640,
                      damage=17, reach=130, height=170,
                      min_range=0, max_range=280, cooldown=5400,
                      hits=3, around=True,
                      hit_sound="siegrid_mangual")  # suena en cada una de las 3 vueltas

    # "Leaps into the air while spinning her flail, before swinging it forwards
    # right as she lands": sube durante el windup, cae avanzando y el golpe
    # solo existe al tocar el piso.
    JUMP_SWING = Move("jump_swing", "jump_swing",
                      telegraph=520, windup=980, active=340, recovery=280,
                      damage=26, reach=75, height=150, advance=10,
                      min_range=140, max_range=640, cooldown=4200,
                      rise=160,
                      hit_sound="siegrid_mangual_suelo")  # suena al aterrizar

    # ------------------------------------------------- fase II: forma Blighted
    HAND_STRIKE = Move("hand_strike", "hand_strike",
                       telegraph=1445, windup=430, active=210, recovery=420,
                       damage=24, reach=460, height=190, advance=6,
                       min_range=0, max_range=340, cooldown=1900,
                       followup="hand_strike_2", followup_chance=0.55,
                       hit_sound="siegrid_zarpazo")

    # Segundo tajo del combo: no se elige solo, solo se encadena.
    HAND_STRIKE_2 = Move("hand_strike_2", "hand_strike",
                         telegraph=375, windup=280, active=200, recovery=430,
                         damage=28, reach=470, height=200, advance=8,
                         selectable=False,
                         hit_sound="siegrid_zarpazo", announce=False)

    # Embestida a ras de suelo que termina en tajo ascendente (hitbox alto).
    DASH_SLASH = Move("dash_slash", "dash_slash",
                      telegraph=1255, windup=620, active=800, recovery=220,
                      damage=24, reach=155, height=140, advance=16,
                      min_range=190, max_range=760, cooldown=3400,
                      finish_at=0.62, finish_reach=150, finish_height=250,
                      finish_damage=32,
                      hit_sound="siegrid_embestida",
                      finish_sound="siegrid_barrido")

    GROUND_SLAM = Move("ground_slam", "ground_slam",
                       telegraph=785, windup=1090, active=450, recovery=240,
                       damage=34, reach=360, height=130,
                       min_range=0, max_range=620, cooldown=4600,
                       rise=190, vertical=True,
                       hit_sound="siegrid_aplastar")  # suena al aterrizar

    PHASE1_MOVES = [FLAIL_SWING, FLAIL_SPIN, JUMP_SWING]
    # La wiki los presenta como añadidos ("gains the following attacks"), pero
    # la segunda forma es otra criatura y NO lleva mangual: los tres ataques de
    # la fase I no tienen con qué ejecutarse. Se queda solo con su repertorio,
    # que es exactamente el que describe la wiki para esta forma.
    PHASE2_MOVES = [HAND_STRIKE, DASH_SLASH, GROUND_SLAM]

    ALL_MOVES = {m.name: m for m in PHASE2_MOVES + [HAND_STRIKE_2]}

    # Altura en píxeles que debe medir el cuerpo visible en cada fase (Lilie
    # mide ~85), de la que se deducen width/height. Cada tanda de arte trae su
    # propio lienzo — el de la fase I es casi cuadrado y el de la fase II es
    # 3:1 por el rugido y los tajos rojos — así que fijar un tamaño a mano
    # deformaría una de las dos.
    BODY_HEIGHT = {1: 136, 2: 215}

    def __init__(self, x, y, width=220, height=200, max_health=600):
        super().__init__(x, y, width, height, max_health, color=(120, 118, 130))

        self.facing_right = False
        self.phase = 1
        # Canon: la transformación llega casi con la barra vacía, ~10% de vida.
        self.phase2_threshold = max_health * 0.10
        self.base_width = width
        self.base_height = height
        self.walk_speed = 1.7
        self.speed_mult = 1.0        # la fase II ejecuta los mismos moves más rápido
        self.contact_damage = 10
        self.contact_cooldown = 0
        self.contact_interval = 800

        self.frame_index = 0
        self.anim_timer = 0
        self.anim_speed = 110
        self.sprite_sets = {p: self._load_animations(p) for p in (1, 2)}
        self.animations, self.animation_bounds, self.animation_cores = self.sprite_sets[1]
        self.width, self.height = self._size_for_phase(1)

        # Temporizadores del motor de combate
        self.action_timer = 0        # ms transcurridos dentro del movimiento actual
        self.current_move = None
        self.move_phase = None       # "windup" | "active" | "recovery"
        self.cooldowns = {}          # nombre de movimiento -> ms restantes
        self.think_timer = 0         # pausa entre movimientos (ms)
        self.attack_hitbox = pygame.Rect(0, 0, 0, 0)
        self._hit_this_swing = False
        self._hit_segment = -1       # ventana de daño actual dentro de un multigolpe
        self._sound_segment = None   # ventana cuyo sonido de golpe ya se lanzó
        self._in_finisher = False
        self.draw_offset_y = 0

        self.transition_duration = 1600
        self.transition_timer = 0

        # Tarda un momento en darse vuelta: esa ventana es la que habilita el
        # golpe hacia atrás de la fase II.
        self.turn_delay = 340
        self.turn_timer = 0

        self.vel_y = 0

    # ------------------------------------------------------------------ arte

    STATES = ["idle", "walk", "run", "flail_swing", "flail_spin", "jump_swing",
              "transition", "hand_strike", "dash_slash",
              "ground_slam", "hurt", "dead"]

    # Si a un estado le falta carpeta propia se cae al primero disponible de
    # esta cadena: así la fase II puede reutilizar el mangual de la fase I y
    # nada queda sin dibujar.
    FALLBACKS = {
        "walk": ["idle"],
        "run": ["walk", "idle"],
        # Las cadenas apuntan a los dos repertorios: en la fase I existe el
        # mangual y en la fase II las garras, así que cada estado busca primero
        # el arte propio de su fase y recién después cae en idle.
        "flail_swing": ["hand_strike", "idle"],
        "flail_spin": ["flail_swing", "hand_strike", "idle"],
        "jump_swing": ["ground_slam", "flail_swing", "idle"],
        "hand_strike": ["flail_swing", "idle"],
        "dash_slash": ["run", "walk", "idle"],
        "ground_slam": ["jump_swing", "flail_swing", "idle"],
        "transition": ["hurt", "idle"],
        "hurt": ["idle"],
        "dead": ["hurt", "idle"],
    }

    def _load_animations(self, phase):
        """Carga un set de sprites por estado desde
        Assets/Enemy/Guardian_Siegrid/fase{N}/<estado>/. La fase I sale de
        Tools/importar_sprites_siegrid.py y la fase II se deriva de ella con
        Tools/derivar_fase2_siegrid.py. Si no hay arte todavía devuelve dicts
        vacíos para que draw() use el rectángulo de color de Enemy."""
        base = os.path.join(self.SPRITE_FOLDER, f"fase{phase}")

        animations = {}
        for state in self.STATES:
            if not os.path.isdir(os.path.join(con.ASSETS_PATH, base, state)):
                continue
            frames = Character._load_frames(os.path.join(base, state), state, 0)
            if frames:
                animations[state] = frames

        if not animations:
            return {}, {}, {}

        default = animations.get("idle", next(iter(animations.values())))
        for state in self.STATES:
            if state in animations:
                continue
            for alt in self.FALLBACKS.get(state, []):
                if alt in animations:
                    animations[state] = animations[alt]
                    break
            else:
                animations[state] = default

        # Dos medidas por frame: el bounding box completo (hitbox del cuerpo)
        # y el "núcleo" (el torso sin el mangual extendido), que es de donde
        # nacen los golpes.
        # Dos medidas por frame: el bounding box completo (hitbox del cuerpo)
        # y el "núcleo" (el torso sin el mangual extendido), que es de donde
        # nacen los golpes. Se cachean por id de lista porque varios estados
        # comparten la misma animación vía FALLBACKS.
        cache = {}
        cuerpos, nucleos = {}, {}
        for estado, frames in animations.items():
            clave = id(frames)
            if clave not in cache:
                cache[clave] = ([Character._alpha_bounds(f) for f in frames],
                                [Character._core_bounds(f) for f in frames])
            cuerpos[estado], nucleos[estado] = cache[clave]
        return animations, cuerpos, nucleos

    def _size_for_phase(self, phase):
        """width/height que hacen que el cuerpo mida BODY_HEIGHT[fase] píxeles,
        conservando la proporción del lienzo de esa fase."""
        animations, cuerpos, _ = self.sprite_sets[phase]
        frames = animations.get("idle")
        if not frames:
            return self.base_width, self.base_height
        caja = cuerpos["idle"][0]
        if not caja.height:
            return self.base_width, self.base_height
        raw = frames[0]
        alto = round(self.BODY_HEIGHT[phase] * raw.get_height() / caja.height)
        ancho = round(alto * raw.get_width() / raw.get_height())
        return ancho, alto

    @property
    def has_sprites(self):
        return bool(self.animations)

    # -------------------------------------------------------------- combate

    @property
    def moves(self):
        return self.PHASE1_MOVES if self.phase == 1 else self.PHASE2_MOVES

    def take_damage(self, amount):
        if self.state in ("dead", "transition"):
            return
        super().take_damage(amount)

        if self.state == "dead":
            Sonidos.reproducir("siegrid_muerte")
            self.current_move = None
            self.attack_hitbox = pygame.Rect(0, 0, 0, 0)
            self.frame_index = 0
            self.anim_timer = 0
        elif self.state == "hurt":
            Sonidos.reproducir("siegrid_golpeada")

        if self.state != "dead" and self.phase == 1 and self.health <= self.phase2_threshold:
            self._enter_phase2()

    def _enter_phase2(self):
        """Transformación de la wiki: al ~10% de vida muta y vuelve a llenar
        la barra entera. Se vuelve más rápida y golpea más fuerte."""
        self.phase = 2
        self.health = self.max_health
        Sonidos.reproducir("siegrid_rugido")
        if self.sprite_sets[2][0]:
            self.animations, self.animation_bounds, self.animation_cores = self.sprite_sets[2]

        # Crece manteniendo los pies en el piso y el centro donde estaba.
        nuevo_w, nuevo_h = self._size_for_phase(2)
        self.x -= (nuevo_w - self.width) // 2
        self.y -= nuevo_h - self.height
        self.width, self.height = nuevo_w, nuevo_h

        self.state = "transition"
        self.transition_timer = self.transition_duration
        self.current_move = None
        self.move_phase = None
        self.cooldowns.clear()
        self.attack_hitbox = pygame.Rect(0, 0, 0, 0)
        self.walk_speed = 3.4
        self.speed_mult = 1.25
        self.contact_damage = 16
        self.invuln_timer = self.transition_duration
        self.color = (128, 62, 74)
        self.frame_index = 0
        self.anim_timer = 0

    def _distance_to(self, target):
        return target.hitbox.centerx - self.hitbox.centerx

    def _is_behind(self, distance):
        """True si Lilie quedó a la espalda de Siegrid (todavía no giró)."""
        return (distance > 0) != self.facing_right

    def _pick_move(self, distance):
        candidates = []
        for m in self.moves:
            if not m.selectable or self.cooldowns.get(m.name, 0) > 0:
                continue
            if m.min_range <= abs(distance) <= m.max_range:
                candidates.append(m)
        return random.choice(candidates) if candidates else None

    def _start_move(self, move):
        self.current_move = move
        self.move_phase = "windup"
        self.action_timer = 0
        self.state = move.state
        self.frame_index = 0
        self.anim_timer = 0
        self._hit_this_swing = False
        self._hit_segment = -1
        self._sound_segment = None
        self._in_finisher = False
        self.cooldowns[move.name] = move.cooldown
        if move.rise:
            self.vel_y = 0
        # Suena al empezar el windup, que es justo la ventana en la que el
        # jugador todavía puede reaccionar. Los movimientos sin daño (si los
        # hubiera) no avisan.
        if move.damage > 0 and move.announce:
            self.avisar_ataque()

    def _end_move(self):
        move = self.current_move
        self.current_move = None
        self.move_phase = None
        self.action_timer = 0
        self.attack_hitbox = pygame.Rect(0, 0, 0, 0)
        self._in_finisher = False

        # "This may be followed up by a second slash": el combo se encadena sin
        # volver a idle.
        if move is not None and move.followup and random.random() < move.followup_chance:
            nxt = self.ALL_MOVES.get(move.followup)
            if nxt is not None:
                self._start_move(nxt)
                return

        self.think_timer = (random.randint(240, 560) if self.phase == 2
                            else random.randint(460, 920))
        self.state = "idle"
        self.frame_index = 0

    def _core_rect(self):
        """Rect del torso en pantalla, sin el mangual extendido ni la polvareda.

        self.hitbox abarca TODO lo dibujado, así que en el frame del golpe su
        borde delantero ya está en la punta del mangual: si el hitbox de ataque
        naciera ahí, quedaría íntegramente en el aire, más allá del arma."""
        if not self.has_sprites:
            return self.hitbox

        frames = self.animations[self.state]
        i = self.frame_index % len(frames)
        raw = frames[i]
        core = self.animation_cores[self.state][i]

        sx = self.width / raw.get_width()
        sy = self.height / raw.get_height()
        w = max(1, round(core.width * sx))
        h = max(1, round(core.height * sy))
        x = round(core.x * sx)
        y = round(core.y * sy)
        if not self.facing_right:
            x = self.width - x - w
        return pygame.Rect(self.x + x, self.y + y + self.draw_offset_y, w, h)

    def _build_attack_hitbox(self, move):
        reach = move.finish_reach if self._in_finisher else move.reach
        height = move.finish_height if self._in_finisher else move.height
        if reach <= 0:
            return pygame.Rect(0, 0, 0, 0)

        # Todos los golpes se anclan al torso, no al sprite completo: así
        # "reach" mide desde el cuerpo y el arma dibujada cae dentro del rect.
        nucleo = self._core_rect()

        if move.vertical:
            # Onda expansiva: nace a los pies del jefe y se abre a los dos lados.
            return pygame.Rect(nucleo.centerx - reach // 2,
                               nucleo.bottom - height,
                               reach, height)
        if move.around:
            # El mangual gira alrededor suyo: golpea por izquierda y derecha.
            return pygame.Rect(nucleo.centerx - reach,
                               nucleo.centery - height // 2,
                               reach * 2, height)

        top = nucleo.centery - height // 2
        if self.facing_right:
            return pygame.Rect(nucleo.right, top, reach, height)
        return pygame.Rect(nucleo.left - reach, top, reach, height)

    def _reproducir_golpe(self, move):
        """Lanza el sonido del golpe una vez por ventana de daño. Se llama
        recién cuando el hitbox existe de verdad, así los ataques que saltan
        (jump_swing, ground_slam) suenan al aterrizar y no en el aire."""
        clave = "fin" if self._in_finisher else (self._hit_segment if move.hits > 1 else 0)
        if clave == self._sound_segment:
            return
        self._sound_segment = clave
        sonido = move.finish_sound if self._in_finisher and move.finish_sound else move.hit_sound
        if sonido:
            Sonidos.reproducir(sonido)

    def _apply_attack(self, target):
        if self._hit_this_swing or target is None:
            return
        if not self.attack_hitbox.colliderect(target.hitbox):
            return
        self._hit_this_swing = True
        move = self.current_move
        damage = move.finish_damage if self._in_finisher else move.damage
        self._damage_target(target, damage)

    @staticmethod
    def _damage_target(target, amount):
        if hasattr(target, "take_damage"):
            target.take_damage(amount)
        elif hasattr(target, "pv"):
            target.pv = max(0, target.pv - amount)

    # --------------------------------------------------------------- update

    def update(self, dt, target=None):
        if self.state == "dead":
            # La animación de muerte corre una sola vez y se congela en el
            # último frame (el cadáver queda en pantalla).
            frames = self.animations.get("dead")
            if frames and self.frame_index < len(frames) - 1:
                self.anim_timer += dt
                if self.anim_timer >= self.anim_speed:
                    self.anim_timer -= self.anim_speed
                    self.frame_index += 1
            self.attack_hitbox = pygame.Rect(0, 0, 0, 0)
            return

        if self.invuln_timer > 0:
            self.invuln_timer -= dt
        for name in list(self.cooldowns):
            self.cooldowns[name] = max(0, self.cooldowns[name] - dt)

        if self.state == "transition":
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                self.state = "idle"
                self.think_timer = 400
            self._advance_animation(dt)
            self._sync_body()
            return

        if self.state == "hurt":
            self.hurt_timer -= dt
            if self.hurt_timer <= 0:
                self.state = "idle" if self.current_move is None else self.current_move.state

        distance = self._distance_to(target) if target is not None else 0

        if self.current_move is not None:
            self._update_move(dt, target)
        else:
            self._update_idle(dt, target, distance)

        self._advance_animation(dt)
        self._sync_body()
        self._update_contact_damage(dt, target)

    def _update_facing(self, dt, distance):
        """No gira instantáneamente: si Lilie la cruza tarda turn_delay ms en
        darse vuelta, y en esa ventana queda expuesta al golpe de espalda."""
        wants_right = distance > 0
        if wants_right == self.facing_right:
            self.turn_timer = 0
            return
        self.turn_timer += dt
        if self.turn_timer >= self.turn_delay:
            self.facing_right = wants_right
            self.turn_timer = 0

    def _update_contact_damage(self, dt, target):
        """Chocar contra el cuerpo del jefe también lastima, pero como mucho
        una vez cada contact_interval para que caminarle encima no borre a
        Lilie en un par de frames."""
        self.contact_cooldown = max(0, self.contact_cooldown - dt)
        if target is None or self.contact_cooldown > 0:
            return
        if self.hitbox.colliderect(target.hitbox):
            self._damage_target(target, self.contact_damage)
            self.contact_cooldown = self.contact_interval

    def _update_idle(self, dt, target, distance):
        if self.think_timer > 0:
            # Mientras se recupera del golpe anterior NO gira: esa es la
            # ventana en la que Lilie puede colocarse a su espalda.
            self.think_timer -= dt
            return

        if target is None:
            self.state = "idle"
            return

        # De espaldas no ataca: no hay animación de golpe hacia atrás, así que
        # cualquier ataque se vería al frente mientras el daño ocurre detrás.
        # Gasta el tiempo dándose vuelta, y esa es la ventana para castigarla.
        if self._is_behind(distance):
            self._update_facing(dt, distance)
            self.state = "idle"
            return

        move = self._pick_move(distance)
        if move is not None:
            self._start_move(move)
            return

        # Sin movimiento disponible: acercarse al jugador.
        if abs(distance) > 90:
            self.x += self.walk_speed if distance > 0 else -self.walk_speed
            self.state = "run" if self.phase == 2 else "walk"
        else:
            self.state = "idle"

    def _update_move(self, dt, target):
        move = self.current_move
        self.action_timer += dt * self.speed_mult

        # Aviso: se queda quieta en la pose de preparación mientras suena la
        # alerta. Todo lo de abajo mide el tiempo ya descontado el telegraph,
        # así que los tramos de la animación no se corren.
        t = self.action_timer - move.telegraph
        if t < 0:
            self.move_phase = "telegraph"
            self.attack_hitbox = pygame.Rect(0, 0, 0, 0)
            return

        if t < move.windup:
            self.move_phase = "windup"
            self.attack_hitbox = pygame.Rect(0, 0, 0, 0)
            if move.rise:
                self.y -= move.rise * (dt * self.speed_mult / move.windup)
            return

        if t < move.windup + move.active:
            self.move_phase = "active"
            elapsed = t - move.windup
            progress = elapsed / move.active

            # Tramo final con otra geometría (el tajo ascendente de la
            # embestida): se reinicia el flag para que pueda pegar de nuevo.
            if move.finish_at is not None and progress >= move.finish_at and not self._in_finisher:
                self._in_finisher = True
                self._hit_this_swing = False

            # Multigolpe: cada vuelta del mangual es una ventana de daño nueva.
            if move.hits > 1:
                segment = min(move.hits - 1, int(progress * move.hits))
                if segment != self._hit_segment:
                    self._hit_segment = segment
                    self._hit_this_swing = False

            if move.advance and not self._in_finisher:
                self.x += move.advance if self.facing_right else -move.advance

            if move.rise:
                # Caída rápida hasta el piso; el golpe solo existe al aterrizar.
                self.vel_y += con.GRAVITY * 3
                self.y = min(con.GROUND_Y - self.height, self.y + self.vel_y)
                if self.y + self.height < con.GROUND_Y:
                    self.attack_hitbox = pygame.Rect(0, 0, 0, 0)
                    return
                self.vel_y = 0

            # El frame se adelanta ANTES de armar el rect. update() vuelve a
            # llamar a _advance_animation después, pero para un ataque el
            # frame sale de action_timer (que ya se incrementó arriba), así
            # que el resultado es el mismo y no hay efecto doble. Sin esto el
            # golpe se calculaba con la pose del frame anterior.
            self._advance_animation(0)
            self._sync_body()
            self.attack_hitbox = self._build_attack_hitbox(move)
            self._reproducir_golpe(move)
            self._apply_attack(target)
            return

        if t < move.anim_duration:
            self.move_phase = "recovery"
            self.attack_hitbox = pygame.Rect(0, 0, 0, 0)
            return

        self._end_move()

    def _advance_animation(self, dt):
        if not self.has_sprites:
            return
        frames = self.animations.get(self.state)
        if not frames:
            return

        # Los ataques y la transición son animaciones de una sola pasada: el
        # frame se deduce del avance del movimiento para que el golpe visual
        # caiga junto con el hitbox activo, en vez de correr en loop aparte.
        oneshot = self._oneshot_progress()
        if oneshot is not None:
            self.frame_index = min(len(frames) - 1, int(oneshot * len(frames)))
            return

        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer -= self.anim_speed
            self.frame_index = (self.frame_index + 1) % len(frames)

    def _oneshot_progress(self):
        if self.state == "transition":
            return 1 - (self.transition_timer / self.transition_duration)
        move = self.current_move
        if move is not None and self.state == move.state:
            # El giro del mangual son tres vueltas: la animación se repite una
            # vez por vuelta en lugar de estirarse a lo largo de todo el move.
            # El telegraph queda fuera del cálculo: durante el aviso el
            # progreso es 0, o sea el primer frame.
            progress = max(0.0, self.action_timer - move.telegraph) / move.anim_duration
            if move.hits > 1:
                return (progress * move.hits) % 1.0
            return progress
        return None

    def _sync_body(self):
        self.y = min(self.y, con.GROUND_Y - self.height)
        if not self.has_sprites:
            self.hitbox.update(self.x, self.y, self.width, self.height)
            return

        Character._sync_hitbox(self)
        # Cada animación deja distinta cantidad de lienzo transparente debajo
        # de los pies (las de plantilla casi nada, las v3 unos 30px), así que
        # dibujar siempre en self.y haría que el jefe flotara y rebotara al
        # cambiar de estado. Se compensa bajando el sprite hasta que los
        # píxeles visibles apoyen en self.y + self.height.
        self.draw_offset_y = self.height - (self.hitbox.bottom - self.y)
        self.hitbox.y += self.draw_offset_y

        # A lo ancho, el cuerpo es el núcleo y no todo lo dibujado: los tajos
        # rojos y la explosión de la fase II ocupan cientos de píxeles, y con
        # el bounding box completo Lilie podría dañarla tocando un efecto a
        # media pantalla, y comerse daño por contacto en el mismo lugar.
        nucleo = self._core_rect()
        self.hitbox.x = nucleo.x
        self.hitbox.width = nucleo.width

    # ----------------------------------------------------------------- draw

    def draw(self, screen):
        if self.state == "dead" and not self.has_sprites:
            return

        if self.has_sprites:
            frame, _ = Character._get_scaled_frame(self)
            if self.state == "hurt":
                frame = frame.copy()
                frame.fill((255, 90, 90), special_flags=pygame.BLEND_RGB_ADD)
            screen.blit(frame, (self.x, self.y + self.draw_offset_y))
            if self.show_hitbox:
                pygame.draw.rect(screen, (255, 0, 0), self.hitbox, 2)
        else:
            color = (255, 255, 255) if self.state == "hurt" else self.color
            pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
            if self.show_hitbox:
                pygame.draw.rect(screen, (255, 0, 0), self.hitbox, 2)

        if self.show_hitbox and self.attack_hitbox.width:
            pygame.draw.rect(screen, (255, 140, 0), self.attack_hitbox, 2)

        if self.state != "dead":
            self._draw_health_bar(screen)
