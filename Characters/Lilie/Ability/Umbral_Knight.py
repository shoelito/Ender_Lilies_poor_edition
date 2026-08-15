from Characters.Ability.Ability import Ability
import json

with open("SavedCampaing/saved1.json", "r") as f:
    saved = json.load(f)


class Umbral_Knight(Ability):
    def __init__(self):
        super().__init__(
            name="Umbral Knight", 
            cooldown = 0.0, 
            uses = 99999, 
            baseDamage = 50, 
            level = saved["abilities"][0]["level"], 
            frames = [],
            animation_speed = 4,
            scale = 0.35,
            offset_x = 30, # Si es positivo, aparece más adelante
            offset_y = -75) # Si es negativo, aparece más arriba
        self._load_frames()

    def Counter(self):
        pass

    def name(self):
        return self.name

    def _load_frames(self):
        super()._load_frames("Assets/Lilie/Ability/Umbral_Knight", "ataque", 6)