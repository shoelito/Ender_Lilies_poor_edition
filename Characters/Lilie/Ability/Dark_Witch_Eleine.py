from Characters.Ability.Ability import Ability
import json

with open("SavedCampaing/saved1.json", "r") as f:
    saved = json.load(f)


class Dark_Witch_Eleine(Ability):
    def __init__(self):
        super().__init__(
            name="Dark Witch Eleine",
            cooldown=0.0,
            uses=70,
            baseDamage=50,
            level=saved["abilities"][5]["level"],
            frames=[],
            animation_speed=4,
            scale=0.35,
            offset_x=30, # Si es positivo, aparece más adelante
            offset_y=-40) # Si es negativo, aparece más arriba
        self._load_frames()

    def name(self):
        return self.name

    def _load_frames(self):
        super()._load_frames("Assets/Lilie/Ability/Dark_Witch_Eleine", "carmesi", 8)