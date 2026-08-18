"""Descriptor de un golpe de Guardian Siegrid."""


# Cada movimiento del jefe se describe con los mismos campos, así el mismo
# motor de estados sirve para las dos fases: solo cambia la tabla.
#   state          -> animación que se reproduce
#   telegraph      -> ms de aviso ANTES del windup: se queda en el primer frame
#                     de la animación mientras suena la alerta, sin hitbox ni
#                     avance. Sirve para dar tiempo de reacción sin tocar el
#                     resto de los tiempos (el frame mostrado sale del avance
#                     dentro de windup+active+recovery, así que estirar el
#                     windup a secas descolocaría la ventana activa).
#   windup/active/recovery -> ms de preparación, de hitbox activo y de recuperación
#   damage         -> daño al jugador si el hitbox activo lo toca
#   reach/height   -> tamaño del hitbox del golpe (reach se mide desde el frente)
#   advance        -> px/frame que el jefe se desplaza hacia adelante mientras ataca
#   min_range/max_range -> distancia horizontal al jugador para poder elegirlo
#   cooldown       -> ms antes de poder repetir ESE movimiento
#   hits           -> cuántas ventanas de daño distintas hay dentro de "active"
#   rise           -> px que salta durante el windup (cae durante el active)
#   around         -> el hitbox nace centrado en ella y golpea a ambos lados
#   vertical       -> onda expansiva a ras de suelo, centrada en sus pies
#   finish_*       -> segundo golpe (distinta geometría) al final del active
#   followup       -> nombre de otro movimiento que puede encadenarse al terminar
#   hit_sound      -> suena en el instante en que el golpe se vuelve peligroso
#                     (no al empezar el movimiento: para eso está pre_ataque).
#                     En los multigolpe suena una vez por cada ventana de daño,
#                     y en los que saltan espera a que toque el suelo.
#   finish_sound   -> sonido propio del remate, cuando el move tiene finish_at
#   announce       -> si lanza el aviso pre_ataque. Los encadenados lo apagan:
#                     el jugador ya fue avisado por el golpe anterior y el aviso
#                     todavía está sonando.
class Move:
    def __init__(self, name, state, windup, active, recovery, damage, reach, height,
                 telegraph=0, advance=0, min_range=0, max_range=9999, cooldown=0, hits=1,
                 rise=0, around=False, vertical=False, selectable=True,
                 finish_at=None, finish_reach=0, finish_height=0, finish_damage=0,
                 followup=None, followup_chance=0.0,
                 hit_sound=None, finish_sound=None, announce=True):
        self.name = name
        self.state = state
        self.telegraph = telegraph
        self.windup = windup
        self.active = active
        self.recovery = recovery
        self.damage = damage
        self.reach = reach
        self.height = height
        self.advance = advance
        self.min_range = min_range
        self.max_range = max_range
        self.cooldown = cooldown
        self.hits = hits
        self.rise = rise
        self.around = around
        self.vertical = vertical
        self.selectable = selectable
        self.finish_at = finish_at
        self.finish_reach = finish_reach
        self.finish_height = finish_height
        self.finish_damage = finish_damage
        self.followup = followup
        self.followup_chance = followup_chance
        self.hit_sound = hit_sound
        self.finish_sound = finish_sound
        self.announce = announce

    @property
    def duration(self):
        return self.telegraph + self.windup + self.active + self.recovery

    @property
    def anim_duration(self):
        """Tramo que consume la animación. El telegraph queda fuera: durante
        el aviso el sprite se mantiene en el primer frame."""
        return self.windup + self.active + self.recovery
