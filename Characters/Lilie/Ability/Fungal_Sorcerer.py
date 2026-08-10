from ..Ability import Ability
import json

with open("SavedCampaing/saved1.json", "r") as f:
    saved = json.load(f)


class Fungal_Sorcerer(Ability):
    def __init__(self):
        super().__init__(
            name="Fungal Sorcerer",
            cooldown=0.0,
            uses=99999,
            baseDamage=50,
            level=saved["abilities"][3]["level"],
            frames=[])

    def Attack(self, screen):
        pass

    def Update(self):
        pass

    def ResetUses(self):
        pass