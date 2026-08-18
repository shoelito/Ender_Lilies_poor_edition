"""Bruja Oscura Eleine, jefa de área del Bosque de las Brujas."""
import math
import random

import pygame

import Constantes as con
from Characters.Enemy.EnemyClass import Enemy
from Characters.Enemy.Proyectil import Proyectil, abanico, circulo
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
      - Justo después de las bolas de fuego o las esferas se teletransporta
        en diagonal por encima de Lilie y ataca con las enredaderas del vestido.
      - Se teletransporta a lo alto de la sala y suelta dos oleadas de esferas
        en todas direcciones.

    La wiki la describe además como muy susceptible al daño por aturdimiento;
    eso queda pendiente porque todavía no hay sistema de aturdimiento.
    """

    VIDEO_MUERTE = "eleine"

    # Cuánto antes del disparo suena la alerta. Eleine es de reacción rápida:
    # avisa medio segundo antes, mucho menos que el segundo y medio de Siegrid.
    AVISO_MS = 500

    # ------------------------------------------------------------- hechizos
    CONO_FUEGO = Hechizo("cono_fuego", aviso=AVISO_MS, windup=260, recovery=520,
                         cooldown=3200, damage=18, max_range=900)

    ESFERA = Hechizo("esfera", aviso=AVISO_MS, windup=200, recovery=420,
                     cooldown=2400, damage=22, max_range=1100)

    # Fase II: la misma esfera, pero sale dos veces seguidas.
    ESFERA_DOBLE = Hechizo("esfera_doble", aviso=AVISO_MS, windup=200, recovery=460,
                           cooldown=2600, damage=22, descargas=2, intervalo=340,
                           max_range=1100)

    TORBELLINO = Hechizo("torbellino", aviso=AVISO_MS, windup=320, recovery=640,
                         cooldown=7000, damage=30, max_range=900)

    # Fase III: no se elige sola, se encadena a los otros ataques.
    ENREDADERAS = Hechizo("enredaderas", aviso=AVISO_MS, windup=240, recovery=520,
                          cooldown=0, damage=26, selectable=False)

    LLUVIA_ESFERAS = Hechizo("lluvia_esferas", aviso=AVISO_MS, windup=380, recovery=720,
                             cooldown=8000, damage=20, descargas=2, intervalo=520)

    PHASE1 = [CONO_FUEGO, ESFERA]
    PHASE2 = [CONO_FUEGO, ESFERA_DOBLE, TORBELLINO]
    PHASE3 = [CONO_FUEGO, ESFERA_DOBLE, TORBELLINO, LLUVIA_ESFERAS]
    TODOS = {h.name: h for h in PHASE3 + [ESFERA, ENREDADERAS]}

    # "Inmediatamente después" de fuego o esferas, en la fase III.
    CHANCE_ENREDADERAS = 1.0

    ALTURA_VUELO = 250       # px sobre el piso a los que flota
    AMPLITUD_FLOTE = 18      # cuánto sube y baja mientras espera
    DIST_PREFERIDA = 330     # distancia a la que trata de mantenerse

    def __init__(self, x, y=None, width=110, height=160, max_health=420):
        if y is None:
            y = con.GROUND_Y - self.ALTURA_VUELO - height
        super().__init__(x, y, width, height, max_health, color=(120, 40, 95))

        self.facing_right = False
        self.phase = 1
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
        self._pendiente_enredaderas = False

        self.transicion_timer = 0
        self.transicion_duracion = 1200
        self.velocidad = 2.2
        self._flote = random.uniform(0, math.pi * 2)
        self._base_y = float(self.y)

    # ----------------------------------------------------------------- fases
    @property
    def hechizos(self):
        return {1: self.PHASE1, 2: self.PHASE2, 3: self.PHASE3}[self.phase]

    def take_damage(self, amount):
        if self.state == "dead" or self.transicion_timer > 0:
            return
        super().take_damage(amount)

        if self.state == "dead":
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
        self.cooldowns[hechizo.name] = hechizo.cooldown
        if hechizo.damage > 0 and hechizo.telegraph:
            self.avisar_ataque()

    def _terminar_hechizo(self, silencioso=False):
        anterior = self.hechizo
        self.hechizo = None
        self.fase_hechizo = None
        self.action_timer = 0
        if silencioso or anterior is None:
            return

        # Encadenado de la fase III: tras fuego o esferas, salta y barre con
        # las enredaderas.
        if (self.phase == 3
                and anterior.name in ("cono_fuego", "esfera", "esfera_doble")
                and random.random() < self.CHANCE_ENREDADERAS):
            self._pendiente_enredaderas = True
            self._empezar(self.ENREDADERAS)
            return

        self.think_timer = random.randint(320, 700)

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
                                        radius=12, color=(235, 130, 60),
                                        lifetime=4000, nombre="fuego")

        elif hechizo.name in ("esfera", "esfera_doble"):
            ang = math.atan2(ty - y, tx - x)
            self.proyectiles.append(
                Proyectil(x, y, math.cos(ang) * 8.5, math.sin(ang) * 8.5,
                          damage=hechizo.damage, radius=15,
                          color=(170, 90, 235), homing=0.08,
                          lifetime=3000, muere_en_suelo=True,
                          nombre="esfera"))

        elif hechizo.name == "torbellino":
            self.torbellino = Proyectil(x, con.GROUND_Y - 90, 0, 0,
                                        damage=hechizo.damage, radius=52,
                                        color=(120, 70, 175), lifetime=12000,
                                        contact_interval=700, nombre="torbellino")
            self.proyectiles.append(self.torbellino)

        elif hechizo.name == "enredaderas":
            self.proyectiles += abanico(x, y, tx, ty, cantidad=3, apertura=26,
                                        rapidez=7.5, damage=hechizo.damage,
                                        radius=16, color=(90, 150, 90),
                                        lifetime=1400, nombre="enredadera")

        elif hechizo.name == "lluvia_esferas":
            # La segunda oleada va girada para no dejar los mismos huecos.
            desfase = 0.0 if self.descargas_hechas == 0 else math.pi / 12
            self.proyectiles += circulo(x, y, cantidad=12, rapidez=4.8,
                                        desfase=desfase, damage=hechizo.damage,
                                        radius=12, color=(205, 105, 225),
                                        lifetime=5000, nombre="lluvia")

    def _teletransportar(self, target, arriba_del_todo=False):
        if target is None:
            return
        if arriba_del_todo:
            self.x = con.WIDTH // 2 - self.width // 2
            self._base_y = 60
        else:
            # En diagonal por encima de Lilie, del lado del que venía.
            lado = -1 if target.hitbox.centerx > self.hitbox.centerx else 1
            self.x = target.hitbox.centerx + lado * 150 - self.width // 2
            self._base_y = target.hitbox.top - 210
        self.x = max(0, min(con.WIDTH - self.width, self.x))
        self._base_y = max(20, self._base_y)
        self.y = self._base_y

    # --------------------------------------------------------------- update
    def update(self, dt, target=None):
        if self.state == "dead":
            self.proyectiles.clear()
            self.torbellino = None
            return

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
                self._teletransportar(target, arriba_del_todo=True)
            self._empezar(hechizo)
            return

        # Sin hechizo disponible: se reacomoda a su distancia preferida.
        hacia_derecha = target.hitbox.centerx > self.hitbox.centerx
        if distancia > self.DIST_PREFERIDA + 60:
            self.x += self.velocidad if hacia_derecha else -self.velocidad
        elif distancia < self.DIST_PREFERIDA - 60:
            self.x -= self.velocidad if hacia_derecha else -self.velocidad
        self.x = max(0, min(con.WIDTH - self.width, self.x))

    def _update_hechizo(self, dt, target):
        h = self.hechizo
        self.action_timer += dt
        t = self.action_timer - h.telegraph

        if t < 0:
            self.fase_hechizo = "telegraph"
            return

        if t < h.windup:
            self.fase_hechizo = "windup"
            # El teletransporte de las enredaderas ocurre en su windup: aparece
            # encima de Lilie justo antes de barrer.
            if self._pendiente_enredaderas:
                self._pendiente_enredaderas = False
                self._teletransportar(target)
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
        self.hitbox.update(self.x, self.y, self.width, self.height)

    # ----------------------------------------------------------------- draw
    def draw(self, screen):
        for p in self.proyectiles:
            p.draw(screen)
        if self.state == "dead":
            return

        color = (255, 255, 255) if self.state == "hurt" else self.color
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        if self.show_hitbox:
            pygame.draw.rect(screen, (255, 0, 0), self.hitbox, 2)
        self._draw_health_bar(screen)
