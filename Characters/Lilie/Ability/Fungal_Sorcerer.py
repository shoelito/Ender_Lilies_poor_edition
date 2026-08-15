from Characters.Ability.Ability import Ability
import json

with open("SavedCampaing/saved1.json", "r") as f:
    saved = json.load(f)


class Fungal_Sorcerer(Ability):
    def __init__(self):
        super().__init__(
            name="Fungal Sorcerer",
            cooldown=6.0,
            uses=12,
            baseDamage=50,
            level=saved["abilities"][3]["level"],
            frames=[],
            animation_speed=4,
            scale=0.35,
            offset_x=30, # Si es positivo, aparece más adelante
            offset_y=-55) # Si es negativo, aparece más arriba
        self._load_frames()
        # Nota: "Assets/Lilie/Ability/Fungal_Sorcerer/Proyectil" tiene sprites de un
        # proyectil aparte (se aleja del personaje), que Ability.Update() todavía no
        # soporta (solo anima pegado a la posición de Lilie). Queda pendiente para
        # cuando haya un sistema de proyectiles con posición/velocidad propia.

    def name(self):
        return self.name

    def _load_frames(self):
        super()._load_frames("Assets/Lilie/Ability/Fungal_Sorcerer", "ataque", 6)