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
            offset_x=30, # Si es positivo, aparece más adelante
            offset_y=-55) # Si es negativo, aparece más arriba
        self._load_frames()

    def name(self):
        return self.name

    def _load_frames(self):
        super()._load_frames("Assets/Lilie/Ability/Guardian_Siegrid", "ataque", 8)