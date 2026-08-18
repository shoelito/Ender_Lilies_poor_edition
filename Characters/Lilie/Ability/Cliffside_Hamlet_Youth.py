from Characters.Ability.Ability import Ability
import Constantes as con
import json

with open("SavedCampaing/saved1.json", "r") as f:
    saved = json.load(f)


class Cliffside_Hamlet_Youth(Ability):
    def __init__(self):
        level = saved["abilities"][2]["level"]
        # En el juego original el cooldown baja con el nivel: 2.7s de base,
        # 2.4s desde nivel 2, 2.1s desde nivel 4.
        cooldown = 2.1 if level >= 4 else 2.4 if level >= 2 else 2.7
        super().__init__(
            name="Cliffside Hamlet Youth",
            cooldown=cooldown,
            uses=18,
            baseDamage=50,
            level=level,
            frames=[],
            animation_speed=4,
            scale=0.35,
            offset_x=30, # Si es positivo, aparece más adelante (arranca tocando el piso)
            is_projectile=True,
            projectile_speed=7, # con peso físico: forma un arco y cae al piso
            projectile_gravity=con.GRAVITY,
            projectile_launch_vy=-8,
            sound="lanzamiento_gusano",   # al arrojarlo
            impact_sound="impacto_gusano") # al chocar
        self._load_frames()

    def name(self):
        return self.name

    def _load_frames(self):
        super()._load_frames("Assets/Lilie/Ability/Cliffside_Hamlet_Youth", "lanzamiento", 8)