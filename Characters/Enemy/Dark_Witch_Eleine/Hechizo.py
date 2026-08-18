"""Descriptor de un hechizo de la Bruja Oscura Eleine."""


# Un hechizo se describe con la misma idea que los golpes de Siegrid
# (telegraph -> windup -> lanzamiento -> recuperación), salvo que acá no hay
# hitbox pegado al cuerpo: en el momento del lanzamiento nacen proyectiles.
#   aviso       -> ms totales desde que suena pre_ataque hasta el disparo.
#                  De ahí sale el telegraph (el tramo en el que se queda
#                  cargando quieta): es lo que sobra tras descontar el windup.
#   windup      -> ms de la animación de lanzamiento, ya dentro del aviso
#   descargas   -> cuántas veces dispara, separadas por intervalo ms
#   recovery    -> ms de recuperación tras la última descarga
#   min/max_range -> distancia a Lilie para poder elegirlo
class Hechizo:
    def __init__(self, name, aviso, windup, recovery, cooldown,
                 descargas=1, intervalo=0, damage=0,
                 min_range=0, max_range=9999, selectable=True):
        self.name = name
        self.aviso = aviso
        self.telegraph = max(0, aviso - windup)
        self.windup = windup
        self.recovery = recovery
        self.cooldown = cooldown
        self.descargas = descargas
        self.intervalo = intervalo
        self.damage = damage
        self.min_range = min_range
        self.max_range = max_range
        self.selectable = selectable

    @property
    def duration(self):
        return (self.telegraph + self.windup
                + self.intervalo * max(0, self.descargas - 1) + self.recovery)
