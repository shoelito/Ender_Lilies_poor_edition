from Characters.Ability.Ability import Ability
import json

with open("SavedCampaing/saved1.json", "r") as f:
    saved = json.load(f)


class Cliffside_Hamlet_Youth(Ability):
    def __init__(self):
        super().__init__(
            name="Cliffside Hamlet Youth",
            cooldown=2.4,
            uses=18,
            baseDamage=50,
            level=saved["abilities"][2]["level"],
            frames=[],
            animation_speed=4,
            scale=0.35,
            offset_x=30, # Si es positivo, aparece más adelante
            offset_y=-40) # Si es negativo, aparece más arriba
        self._load_frames()

    def name(self):
        return self.name

    def _load_frames(self):
        super()._load_frames("Assets/Lilie/Ability/Cliffside_Hamlet_Youth", "lanzamiento", 8)