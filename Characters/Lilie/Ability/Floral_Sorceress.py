from Characters.Ability.Ability import Ability
import json

with open("SavedCampaing/saved1.json", "r") as f:
    saved = json.load(f)


class Floral_Sorceress(Ability):
    def __init__(self):
        super().__init__(
            name="Floral Sorceress",
            cooldown=4.0,
            uses=12,
            baseDamage=50,
            level=saved["abilities"][4]["level"],
            frames=[],
            animation_speed=5,
            scale=1.0, # los sprites del tornado ya vienen del tamaño de Lilie, no hace falta reducirlos
            offset_x=20, # Si es positivo, aparece más adelante
            offset_y=-20) # Si es negativo, aparece más arriba
        self.attack_zone = 5
        self._load_frames()

    def name(self):
        return self.name

    def _load_frames(self):
        super()._load_frames("Assets/Lilie/Ability/Floral_Sorceress", "tornado", 6)