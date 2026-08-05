from ..Ability import Ability
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
            frames = [])

    def Attack(self, screen):
        pass

    def Update(self):
        pass

    def Counter(self):
        pass

    def ResetUses(self):
        pass