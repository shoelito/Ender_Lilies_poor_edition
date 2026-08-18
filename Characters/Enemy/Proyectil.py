import math
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
    """

    def __init__(self, x, y, vx, vy, damage, radius=13, color=(198, 96, 226), homing=0.0, lifetime=4000, gravity=0.0, contact_interval=None, muere_en_suelo=False, nombre=""):
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

        self.vivo = True
        self._contacto = 0
        self.hitbox = pygame.Rect(0, 0, radius * 2, radius * 2)
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
        if target is not None and self._contacto <= 0 and self.hitbox.colliderect(target.hitbox):
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
