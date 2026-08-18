import math
import os
import re

import pygame
import Constantes as con


class Proyectil:
    """Un disparo enemigo.

    homing          0 = va recto; >0 = corrige el rumbo hacia Lilie cada frame
                    (0.05 apenas se curva, 0.3 persigue con ganas).
                    
    contact_interval  None = muere al primer impacto. Con un valor en ms, en
                    cambio, sobrevive y vuelve a pegar cada ese tiempo.
                    
    muere_en_suelo  True = se deshace al tocar el piso en vez de seguir de
                    largo hasta salir de pantalla.
    frames          Lista de superficies. Sin ella se dibuja el círculo de
                    color, que es el respaldo mientras no hay arte.
    rotar           Orienta el sprite según hacia dónde viaja. El arte se
                    dibuja apuntando a la derecha, así que esto lo alinea con
                    cada dirección del abanico.
    girar           Grados por segundo que el sprite rota sobre sí mismo, para
                    los proyectiles que son un remolino y no apuntan a nada.
    frames_final    Animación de disipación. Mientras el proyectil vive giran
                    los frames normales; en los últimos milisegundos se
                    reproduce esta una sola vez y deja de hacer daño, porque
                    visualmente ya se está apagando.
    hitbox_size     (ancho, alto) explícito. Sin esto el hitbox es un cuadrado
                    de radius*2, que no sirve para formas altas y angostas
                    como el embudo del torbellino.
    """

    def __init__(self, x, y, vx, vy, damage, radius=13, color=(198, 96, 226), homing=0.0, lifetime=4000, gravity=0.0, contact_interval=None, muere_en_suelo=False, frames=None, anim_ms=70, rotar=False, girar=0.0, frames_final=None, anim_ms_final=None, hitbox_size=None, nombre=""):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.damage = damage
        self.radius = radius
        self.color = color
        self.homing = homing
        self.lifetime = lifetime
        self.gravity = gravity
        self.contact_interval = contact_interval
        self.muere_en_suelo = muere_en_suelo
        self.nombre = nombre

        self.frames = frames or []
        self.anim_ms = anim_ms
        self.rotar = rotar
        self.girar = girar
        self._frame = 0
        self._anim_timer = 0
        self._angulo = 0.0

        self.frames_final = frames_final or []
        # Cuánto dura la disipación, al final de la vida del proyectil. Lleva
        # su propio ritmo: el bucle puede girar rápido y el apagado ser lento.
        self._ms_final = len(self.frames_final) * (anim_ms_final or anim_ms)
        self._frame_final = None   # None = todavia no empezo a disiparse

        self.vivo = True
        self._contacto = 0
        ancho, alto = hitbox_size or (radius * 2, radius * 2)
        self.hitbox = pygame.Rect(0, 0, ancho, alto)
        self._sync()

    def _sync(self):
        self.hitbox.center = (round(self.x), round(self.y))

    @property
    def velocidad(self):
        return math.hypot(self.vx, self.vy)

    def update(self, dt, target=None):
        if not self.vivo:
            return False

        self.lifetime -= dt
        if self.lifetime <= 0:
            self.vivo = False
            return False

        if self.homing > 0 and target is not None:
            rapidez = self.velocidad
            dx = target.hitbox.centerx - self.x
            dy = target.hitbox.centery - self.y
            dist = math.hypot(dx, dy) or 1.0
            self.vx += (dx / dist * rapidez - self.vx) * self.homing
            self.vy += (dy / dist * rapidez - self.vy) * self.homing
            nueva = self.velocidad or 1.0
            self.vx = self.vx / nueva * rapidez
            self.vy = self.vy / nueva * rapidez

        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        self._sync()

        if self.frames_final and self.lifetime <= self._ms_final:
            # Tramo de disipacion: el frame sale de cuanto queda de vida, no
            # de un temporizador propio, asi termina justo con el proyectil.
            avance = 1 - max(0, self.lifetime) / self._ms_final
            self._frame_final = min(len(self.frames_final) - 1,
                                    int(avance * len(self.frames_final)))

        if self.frames:
            self._anim_timer += dt
            if self._anim_timer >= self.anim_ms:
                self._anim_timer -= self.anim_ms
                self._frame = (self._frame + 1) % len(self.frames)
            if self.girar:
                self._angulo = (self._angulo + self.girar * dt / 1000.0) % 360

        if self.muere_en_suelo and self.y + self.radius >= con.GROUND_Y:
            self.vivo = False
            return False

        margen = self.radius * 4
        if (self.x < -margen or self.x > con.WIDTH + margen
                or self.y < -margen or self.y > con.HEIGHT + margen):
            self.vivo = False
            return False

        if self._contacto > 0:
            self._contacto -= dt
        if (target is not None and self._frame_final is None and self._contacto <= 0
                and self.hitbox.colliderect(target.hitbox)):
            # Solo se gasta si el golpe entró: si Lilie está esquivando o con
            # i-frames, el proyectil la ATRAVIESA y sigue viaje, en vez de
            # desaparecer sin haber hecho nada.
            if self._danar(target):
                if self.contact_interval is None:
                    self.vivo = False
                    return False
                self._contacto = self.contact_interval

        return True

    def _danar(self, target):
        if hasattr(target, "take_damage"):
            return target.take_damage(self.damage) is not False
        if hasattr(target, "pv"):
            target.pv = max(0, target.pv - self.damage)
            return True
        return False

    def draw(self, screen):
        if self._frame_final is not None and self.frames_final:
            sprite = self.frames_final[self._frame_final]
            screen.blit(sprite, sprite.get_rect(center=self.hitbox.center))
        elif self.frames:
            sprite = self.frames[self._frame % len(self.frames)]
            if self.rotar:
                # pygame gira en sentido antihorario y el eje Y va hacia abajo,
                # asi que el angulo de la velocidad se niega.
                sprite = pygame.transform.rotate(sprite, -math.degrees(math.atan2(self.vy, self.vx)))
            elif self.girar:
                sprite = pygame.transform.rotate(sprite, self._angulo)
            screen.blit(sprite, sprite.get_rect(center=self.hitbox.center))
        else:
            # Respaldo mientras no hay arte.
            pygame.draw.circle(screen, self.color, self.hitbox.center, self.radius)
            pygame.draw.circle(screen, (245, 235, 250), self.hitbox.center, max(2, self.radius // 3))
        if con.SHOW_HITBOX:
            pygame.draw.rect(screen, (255, 200, 0), self.hitbox, 1)


def abanico(x, y, hacia_x, hacia_y, cantidad, apertura, rapidez, **kwargs):
    base = math.atan2(hacia_y - y, hacia_x - x)
    if cantidad == 1:
        angulos = [base]
    else:
        paso = math.radians(apertura) / (cantidad - 1)
        angulos = [base - math.radians(apertura) / 2 + paso * i for i in range(cantidad)]
    return [Proyectil(x, y, math.cos(a) * rapidez, math.sin(a) * rapidez, **kwargs) for a in angulos]


def circulo(x, y, cantidad, rapidez, desfase=0.0, **kwargs):
    return [Proyectil(x, y,math.cos(desfase + 2 * math.pi * i / cantidad) * rapidez,math.sin(desfase + 2 * math.pi * i / cantidad) * rapidez, **kwargs) for i in range(cantidad)]


def cargar_frames(carpeta, escala=1.0):
    """Carga los PNG de una carpeta de Assets ordenados por su número.

    Devuelve [] si la carpeta no existe todavía, para que el proyectil caiga
    en el círculo de respaldo en vez de romper.
    """
    ruta = os.path.join(con.ASSETS_PATH, carpeta)
    if not os.path.isdir(ruta):
        return []

    def numero(nombre):
        m = re.search(r"(\d+)", nombre)
        return (int(m.group(1)) if m else float("inf"), nombre)

    frames = []
    for archivo in sorted(os.listdir(ruta), key=numero):
        if not archivo.lower().endswith(".png"):
            continue
        img = pygame.image.load(os.path.join(ruta, archivo)).convert_alpha()
        if escala != 1.0:
            img = pygame.transform.smoothscale(
                img, (max(1, round(img.get_width() * escala)),
                      max(1, round(img.get_height() * escala))))
        frames.append(img)
    return frames
