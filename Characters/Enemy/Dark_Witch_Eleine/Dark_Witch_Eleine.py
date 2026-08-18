"""Bruja Oscura Eleine, jefa de área del Bosque de las Brujas."""
import math
import os
import random

import pygame

import Constantes as con
import Sonidos
import Mundo
from Characters.CharacterClass import Character
from Characters.Enemy.EnemyClass import Enemy
from Characters.Enemy.Proyectil import Proyectil, abanico, circulo, cargar_frames
from Characters.Enemy.Dark_Witch_Eleine.Hechizo import Hechizo


class Dark_Witch_Eleine(Enemy):
    """Jefa a distancia de TRES fases, siempre en el aire.

    Fase I (100%-66%):
      - Alza el bastón y dispara seis bolas de fuego en cono hacia Lilie.
      - Balancea el bastón y suelta una esfera teledirigida rápida.

    Al ~66% se vuelve invulnerable un momento y suma:
      - La esfera teledirigida sale dos veces seguidas.
      - Deja un torbellino fijo donde está, que dura mucho y pega por
        contacto. Solo puede haber uno a la vez.

    Al ~33% se enfurece y toma una forma monstruosa, sumando:
      - Se teletransporta a lo alto de la sala y suelta dos oleadas de esferas
        en todas direcciones.

    La wiki le da además un cuarto ataque en esta forma: teletransportarse en
    diagonal sobre Lilie y barrer con las enredaderas del vestido. No hay
    animación de enredaderas, así que se sacó en vez de dejarla como unos
    círculos sueltos que no se entienden.

    La wiki la describe además como muy susceptible al daño por aturdimiento;
    eso queda pendiente porque todavía no hay sistema de aturdimiento.
    """

    VIDEO_MUERTE = "eleine"
    # Tema de fondo de cada fase (de Sonidos.MUSICA).
    MUSICA_FASE = {1: "eleine_fase1", 2: "eleine_fase2", 3: "eleine_fase3"}

    # Cuánto antes del disparo suena la alerta. Eleine es de reacción rápida:
    # avisa medio segundo antes, mucho menos que el segundo y medio de Siegrid.
    AVISO_MS = 500

    # Pausa entre un hechizo y el siguiente, por fase. Es el freno principal
    # del ritmo: cuanto mas corta, mas seguido ataca. Se acorta en cada
    # transformacion, asi la pelea se acelera a medida que avanza.
    PAUSA_MS = {
        1: (1500, 2400),
        2: (1050, 1700),
        3: (700, 1150),
    }

    # Multiplicador de los cooldowns por fase. La pausa sola no alcanzaria:
    # sin esto, al acelerar se quedaria esperando a que se liberen los
    # hechizos y el ritmo no subiria tanto como parece.
    COOLDOWN_FASE = {1: 1.0, 2: 0.78, 3: 0.58}

    # ------------------------------------------------------------- hechizos
    CONO_FUEGO = Hechizo("cono_fuego", aviso=AVISO_MS, windup=260, recovery=520,
                         cooldown=4600, damage=18, max_range=900)

    ESFERA = Hechizo("esfera", aviso=AVISO_MS, windup=200, recovery=420,
                     cooldown=3600, damage=22, max_range=1100)

    # Fase II: la misma esfera, pero sale dos veces seguidas.
    ESFERA_DOBLE = Hechizo("esfera_doble", aviso=AVISO_MS, windup=200, recovery=460,
                           cooldown=3800, damage=22, descargas=2, intervalo=340,
                           max_range=1100)

    TORBELLINO = Hechizo("torbellino", aviso=AVISO_MS, windup=320, recovery=640,
                         cooldown=9000, damage=30, max_range=900)

    LLUVIA_ESFERAS = Hechizo("lluvia_esferas", aviso=AVISO_MS, windup=380, recovery=720,
                             cooldown=9000, damage=20, descargas=2, intervalo=520)

    PHASE1 = [CONO_FUEGO, ESFERA]
    PHASE2 = [CONO_FUEGO, ESFERA_DOBLE, TORBELLINO]
    PHASE3 = [CONO_FUEGO, ESFERA_DOBLE, TORBELLINO, LLUVIA_ESFERAS]
    TODOS = {h.name: h for h in PHASE3 + [ESFERA]}

    SPRITE_FOLDER = "Enemy/Dark_Witch_Eleine"
    # Altura en pixeles que debe medir su cuerpo visible (Lilie mide ~85). De
    # ahi salen width/height, respetando la proporcion del lienzo: fijarlos a
    # mano la achataria, porque el sprite es casi cuadrado.
    ALTO_CUERPO = 170

    ALTO_TORBELLINO = 230    # px de alto del embudo ya en pantalla
    # Px sobre el piso a los que flota. No es libre: Lilie salta 194 px y sus
    # habilidades se anclan a sus pies, asi que el mejor ataque en el aire
    # llega a y=447. Con 250 Eleine no bajaba de y=418 y era literalmente
    # inmatable; a 180 queda alcanzable saltando, que es como se pelea contra
    # un jefe que nunca toca el suelo.
    ALTURA_VUELO = 180
    AMPLITUD_FLOTE = 18      # cuánto sube y baja mientras espera
    DIST_PREFERIDA = 330     # distancia a la que trata de mantenerse

    # Vida. Es la jefa mas larga del juego: tres fases y, a diferencia de Siegrid,
    # no se cura al transformarse, asi que los 1800 se reparten enteros entre
    # las tres (1800 -> 1188 -> 594). Siegrid pide 1140 de dano en total porque
    # recupera la barra al mutar.
    def __init__(self, x, y=None, width=110, height=160, max_health=1800):
        if y is None:
            y = con.GROUND_Y - self.ALTURA_VUELO - height
        super().__init__(x, y, width, height, max_health, color=(120, 40, 95))

        self.facing_right = False
        self.phase = 1

        self.frame_index = 0
        self.anim_timer = 0
        self.anim_speed = 130
        self._cargar_arte()
        if self.has_sprites:
            self.width, self.height = self._tamano_desde_arte()
            y = con.GROUND_Y - self.ALTURA_VUELO - self.height
        self.umbral_fase2 = max_health * 0.66
        self.umbral_fase3 = max_health * 0.33

        self.proyectiles = []
        self.torbellino = None      # solo puede haber uno a la vez

        self.hechizo = None
        self.action_timer = 0
        self.fase_hechizo = None    # telegraph | windup | lanzando | recovery
        self.descargas_hechas = 0
        self.cooldowns = {}
        self.think_timer = 0

        self._combate_iniciado = False
        self.transicion_timer = 0
        self.transicion_duracion = 1200
        self.velocidad = 2.2
        self._flote = random.uniform(0, math.pi * 2)
        self.y = y
        self._base_y = float(y)

    # ------------------------------------------------------------------ arte
    def _cargar_arte(self):
        """Carga el cuerpo y los sprites de los proyectiles.

        Si falta alguna carpeta se sigue sin ella: el cuerpo cae al rectangulo
        de color de Enemy y los proyectiles al circulo de respaldo."""
        carpeta = os.path.join(self.SPRITE_FOLDER, "fase1", "vuelo")
        try:
            vuelo = Character._load_frames(carpeta, "vuelo", 0)
        except (FileNotFoundError, OSError):
            vuelo = []

        if vuelo:
            # Todavia tiene una sola animacion de cuerpo, asi que los estados
            # que hereda de Enemy apuntan todos a ella.
            self.animations = {e: vuelo for e in ("idle", "hurt", "dead")}
            bordes = [Character._alpha_bounds(f) for f in vuelo]
            self.animation_bounds = {e: bordes for e in self.animations}
        else:
            self.animations = {}
            self.animation_bounds = {}

        base = os.path.join(self.SPRITE_FOLDER, "proyectiles")
        # El recorte de la bola de fuego es chico al lado de ella; se agranda
        # para que se lea en pantalla.
        self.frames_bolafuego = cargar_frames(os.path.join(base, "bolafuego"), escala=1.5)
        self.frames_esfera = cargar_frames(os.path.join(base, "esfera"))
        # El recorte del torbellino es enorme (475x360); se achica para que el
        # embudo mida ALTO_TORBELLINO en pantalla.
        escala_t = self.ALTO_TORBELLINO / 355.0
        self.frames_torbellino = cargar_frames(
            os.path.join(base, "torbellino"), escala=escala_t)
        self.frames_torbellino_fin = cargar_frames(
            os.path.join(base, "torbellino_fin"), escala=escala_t)

    @property
    def has_sprites(self):
        return bool(self.animations)

    def _tamano_desde_arte(self):
        """width/height que hacen que su cuerpo mida ALTO_CUERPO pixeles,
        conservando la proporcion del lienzo."""
        frames = self.animations["idle"]
        caja = self.animation_bounds["idle"][0]
        if not caja.height:
            return self.width, self.height
        raw = frames[0]
        alto = round(self.ALTO_CUERPO * raw.get_height() / caja.height)
        ancho = round(alto * raw.get_width() / raw.get_height())
        return ancho, alto

    # ----------------------------------------------------------------- fases
    @property
    def hechizos(self):
        return {1: self.PHASE1, 2: self.PHASE2, 3: self.PHASE3}[self.phase]

    def take_damage(self, amount):
        if self.state == "dead" or self.transicion_timer > 0:
            return
        super().take_damage(amount)

        if self.state == "dead":
            Sonidos.parar_musica()
            self._terminar_hechizo(silencioso=True)
            self.proyectiles.clear()
            self.torbellino = None
            return
        if self.phase == 1 and self.health <= self.umbral_fase2:
            self._cambiar_fase(2)
        elif self.phase == 2 and self.health <= self.umbral_fase3:
            self._cambiar_fase(3)

    def _cambiar_fase(self, fase):
        """Se vuelve invulnerable un momento mientras muta."""
        self.phase = fase
        self._terminar_hechizo(silencioso=True)
        self.cooldowns.clear()
        self.transicion_timer = self.transicion_duracion
        self.invuln_timer = self.transicion_duracion
        Sonidos.reproducir("cambio_eleine")
        Sonidos.musica(self.MUSICA_FASE[fase], fundido_ms=400)
        if fase == 2:
            self.velocidad = 2.8
            self.color = (150, 45, 120)
        else:
            self.velocidad = 3.4
            self.color = (185, 50, 90)   # forma enfurecida

    # -------------------------------------------------------------- combate
    def _elegir(self, distancia):
        opciones = [h for h in self.hechizos
                    if h.selectable and self.cooldowns.get(h.name, 0) <= 0
                    and h.min_range <= distancia <= h.max_range]
        # El torbellino es único: mientras el anterior siga en pie, no repite.
        if self.torbellino is not None and self.torbellino.vivo:
            opciones = [h for h in opciones if h.name != "torbellino"]
        return random.choice(opciones) if opciones else None

    def _empezar(self, hechizo):
        self.hechizo = hechizo
        self.action_timer = 0
        self.fase_hechizo = "telegraph" if hechizo.telegraph else "windup"
        self.descargas_hechas = 0
        self.cooldowns[hechizo.name] = hechizo.cooldown * self.COOLDOWN_FASE[self.phase]
        if hechizo.damage > 0 and hechizo.telegraph:
            self.avisar_ataque()

    def _terminar_hechizo(self, silencioso=False):
        anterior = self.hechizo
        self.hechizo = None
        self.fase_hechizo = None
        self.action_timer = 0
        if silencioso or anterior is None:
            return

        self.think_timer = random.randint(*self.PAUSA_MS[self.phase])

    # --------------------------------------------------------- lanzamientos
    def _lanzar(self, hechizo, target):
        """Suelta una descarga del hechizo."""
        if target is None:
            return
        x, y = self.hitbox.centerx, self.hitbox.centery
        tx, ty = target.hitbox.centerx, target.hitbox.centery

        if hechizo.name == "cono_fuego":
            self.proyectiles += abanico(x, y, tx, ty, cantidad=6, apertura=48,
                                        rapidez=6.5, damage=hechizo.damage,
                                        radius=20, color=(235, 130, 60),
                                        lifetime=4000, frames=self.frames_bolafuego,
                                        rotar=True, nombre="fuego")

        elif hechizo.name in ("esfera", "esfera_doble"):
            ang = math.atan2(ty - y, tx - x)
            self.proyectiles.append(
                Proyectil(x, y, math.cos(ang) * 8.5, math.sin(ang) * 8.5,
                          damage=hechizo.damage, radius=20,
                          color=(170, 90, 235), homing=0.08,
                          lifetime=3000, muere_en_suelo=True,
                          frames=self.frames_esfera, girar=180,
                          nombre="esfera"))

        elif hechizo.name == "torbellino":
            # Se apoya en el piso, no flota a su altura: el embudo toca tierra.
            alto = self.ALTO_TORBELLINO
            centro_y = con.GROUND_Y - alto // 2
            # El hitbox es el embudo, más angosto que el remolino dibujado:
            # las volutas de arriba se abren mucho y no deberían pegar.
            self.torbellino = Proyectil(x, centro_y, 0, 0,
                                        damage=hechizo.damage, radius=52,
                                        hitbox_size=(int(alto * 0.55), alto),
                                        color=(120, 70, 175), lifetime=12000,
                                        contact_interval=700,
                                        frames=self.frames_torbellino,
                                        frames_final=self.frames_torbellino_fin,
                                        anim_ms=70, anim_ms_final=200,
                                        nombre="torbellino")
            self.proyectiles.append(self.torbellino)

        elif hechizo.name == "lluvia_esferas":
            # La segunda oleada va girada para no dejar los mismos huecos.
            desfase = 0.0 if self.descargas_hechas == 0 else math.pi / 12
            self.proyectiles += circulo(x, y, cantidad=12, rapidez=4.8,
                                        desfase=desfase, damage=hechizo.damage,
                                        radius=20, color=(205, 105, 225),
                                        lifetime=5000, frames=self.frames_esfera,
                                        girar=180, nombre="lluvia")

    def _teletransportar_arriba(self, target=None):
        """Se planta en lo alto de la sala, que es de donde suelta la lluvia.

        Se ubica sobre Lilie y no en el centro del nivel: con la camara, el
        nivel es mucho mas ancho que la pantalla y el centro podria quedar
        fuera de la vista."""
        centro = target.hitbox.centerx if target is not None else self.hitbox.centerx
        self.x = Mundo.limitar_x(centro - self.width // 2, self.width)
        self._base_y = 60
        self.y = self._base_y

    # --------------------------------------------------------------- update
    def update(self, dt, target=None):
        if self.state == "dead":
            self.proyectiles.clear()
            self.torbellino = None
            return

        if not self._combate_iniciado and target is not None:
            # Mismo criterio que con Siegrid: sin disparador de arena, la
            # pelea empieza cuando el jefe recibe por primera vez a quien
            # enfrentar.
            self._combate_iniciado = True
            Sonidos.musica(self.MUSICA_FASE[self.phase])

        if self.invuln_timer > 0:
            self.invuln_timer -= dt
        for nombre in list(self.cooldowns):
            self.cooldowns[nombre] = max(0, self.cooldowns[nombre] - dt)

        self.proyectiles = [p for p in self.proyectiles if p.update(dt, target)]
        if self.torbellino is not None and not self.torbellino.vivo:
            self.torbellino = None

        if self.transicion_timer > 0:
            self.transicion_timer -= dt
            self._flotar(dt)
            return

        if self.state == "hurt":
            self.hurt_timer -= dt
            if self.hurt_timer <= 0:
                self.state = "idle"

        if target is not None:
            self.facing_right = target.hitbox.centerx > self.hitbox.centerx

        if self.hechizo is not None:
            self._update_hechizo(dt, target)
        else:
            self._update_idle(dt, target)

        self._flotar(dt)

    def _update_idle(self, dt, target):
        if self.think_timer > 0:
            self.think_timer -= dt
            return
        if target is None:
            return

        distancia = abs(target.hitbox.centerx - self.hitbox.centerx)
        hechizo = self._elegir(distancia)
        if hechizo is not None:
            if hechizo.name == "lluvia_esferas":
                # "Se teletransporta a lo alto de la sala" antes de la lluvia.
                self._teletransportar_arriba(target)
            self._empezar(hechizo)
            return

        # Sin hechizo disponible: se reacomoda a su distancia preferida.
        hacia_derecha = target.hitbox.centerx > self.hitbox.centerx
        if distancia > self.DIST_PREFERIDA + 60:
            self.x += self.velocidad if hacia_derecha else -self.velocidad
        elif distancia < self.DIST_PREFERIDA - 60:
            self.x -= self.velocidad if hacia_derecha else -self.velocidad
        self.x = Mundo.limitar_x(self.x, self.width)

    def _update_hechizo(self, dt, target):
        h = self.hechizo
        self.action_timer += dt
        t = self.action_timer - h.telegraph

        if t < 0:
            self.fase_hechizo = "telegraph"
            return

        if t < h.windup:
            self.fase_hechizo = "windup"
            return

        # Primera descarga al terminar el windup; las siguientes cada
        # h.intervalo ms.
        debidas = 1 + int((t - h.windup) // h.intervalo) if h.intervalo else 1
        debidas = min(debidas, h.descargas)
        while self.descargas_hechas < debidas:
            self.fase_hechizo = "lanzando"
            self._lanzar(h, target)
            self.descargas_hechas += 1

        if self.descargas_hechas >= h.descargas:
            fin = h.windup + h.intervalo * max(0, h.descargas - 1)
            if t >= fin + h.recovery:
                self._terminar_hechizo()
            else:
                self.fase_hechizo = "recovery"

    def _flotar(self, dt):
        """Nunca toca el suelo: se mantiene en el aire con un vaivén suave."""
        self._flote += dt / 420.0
        self.y = self._base_y + math.sin(self._flote) * self.AMPLITUD_FLOTE

        if not self.has_sprites:
            self.hitbox.update(self.x, self.y, self.width, self.height)
            return

        frames = self.animations[self.state]
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer -= self.anim_speed
            self.frame_index = (self.frame_index + 1) % len(frames)
        # El hitbox sigue los pixeles visibles, no todo el lienzo.
        Character._sync_hitbox(self)

    # ----------------------------------------------------------------- draw
    def draw(self, screen):
        for p in self.proyectiles:
            p.draw(screen)
        if self.state == "dead":
            return

        if self.has_sprites:
            frame, _ = Character._get_scaled_frame(self)
            if self.state == "hurt":
                frame = frame.copy()
                frame.fill((255, 90, 90), special_flags=pygame.BLEND_RGB_ADD)
            screen.blit(frame, (self.x, self.y))
        else:
            color = (255, 255, 255) if self.state == "hurt" else self.color
            pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        if self.show_hitbox:
            pygame.draw.rect(screen, (255, 0, 0), self.hitbox, 2)
        self._draw_health_bar(screen)
