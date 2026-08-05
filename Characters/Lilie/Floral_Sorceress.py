from ..Ability import Ability
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
            frames=[])
        self.attack_zone = 5

    def Attack(self, screen):
        pass

    def Update(self):
        pass

    def ResetUses(self):
        pass
