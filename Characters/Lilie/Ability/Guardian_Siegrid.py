from Characters.Ability.Ability import Ability
import json

with open("SavedCampaing/saved1.json", "r") as f:
    saved = json.load(f)


class Guardian_Siegrid(Ability):
    def __init__(self):
        super().__init__(
            name="Guardian Siegrid",
            cooldown=4.5,
            uses=13,
            baseDamage=50,
            level=saved["abilities"][1]["level"],
            frames=[],
            animation_speed=5,
            scale=0.35,
            offset_x=30, # Si es positivo, aparece más adelante (Y siempre toca el piso)
            anchor_once=True, # se queda donde se invocó, no sigue a Lilie
            loop_count=3, # recorre la secuencia de sprites 3 veces
            damage_on_loop=True, # hace daño una vez por cada vuelta completa
            loop_sound="siegrid_mangual") # suena en cada una de las tres vueltas
        self._load_frames()

    def name(self):
        return self.name

    def _load_frames(self):
        super()._load_frames("Assets/Lilie/Ability/Guardian_Siegrid", "ataque", 8)